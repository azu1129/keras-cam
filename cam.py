from keras.models import *
from keras.callbacks import *
import keras.backend as K
from model import *
from data import *
import cv2
import argparse

# �g���[�j���O
def train(dataset_path):
        # ���f���擾
        model = get_model()
        
        # �f�[�^�Z�b�g�擾
        X, y = load_inria_person(dataset_path)
        
        print "Training.."
        
        # �r���̃Z�[�u���@���w��
        checkpoint_path="weights.{epoch:02d}-{val_loss:.2f}.hdf5"
        checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_loss', verbose=0, save_best_only=False, save_weights_only=False, mode='auto')
        
        # �w�K�X�^�[�g
        model.fit(X, y, nb_epoch=40, batch_size=32, validation_split=0.2, verbose=1, callbacks=[checkpoint])

# ����
def visualize_class_activation_map(model_path, img_path, output_path):
        # ���f���̃��[�h
        model = load_model(model_path)
        
        # �Ώۉ摜�̓Ǎ���
        original_img = cv2.imread(img_path, 1)
        width, height, _ = original_img.shape

        # ���V�F�C�v
        #Reshape to the network input shape (3, w, h).
        img = np.array([np.transpose(np.float32(original_img), (2, 0, 1))])
        
        #Get the 512 input weights to the softmax.
        class_weights = model.layers[-1].get_weights()[0]     # [CAM] ���[�ƁH�H�H
        final_conv_layer = get_output_layer(model, "conv5_3") # [CAM] ���[�ƁH�H�H
        get_output = K.function([model.layers[0].input], [final_conv_layer.output, model.layers[-1].output]) # [CAM] ���[�ƁH�H�H
        
        # https://keras.io/ja/getting-started/faq/
        [conv_outputs, predictions] = get_output([img]) # �摜�����!
        conv_outputs = conv_outputs[0, :, :, :]         # [CAM] ���[�ƁH�H�H

        # CAM�̐���
        # Create the class activation map.
        
        # �[���N���A
        cam = np.zeros(dtype = np.float32, shape = conv_outputs.shape[1:3]) 
        
        for i, w in enumerate(class_weights[:, 1]): # [CAM] ���[�ƁH�H�H
                cam += w * conv_outputs[i, :, :]    # [CAM] ���[�ƁH�H�H

        print "predictions", predictions
        cam /= np.max(cam)                      # �ő�l�Ő��K��
        cam = cv2.resize(cam, (height, width))  # opencv��numpy�����T�C�Y
        
        heatmap = cv2.applyColorMap(np.uint8(255*cam), cv2.COLORMAP_JET) # �q�[�g�}�b�v�B�֗��I
        heatmap[np.where(cam < 0.2)] = 0 # 0.2��菬��؂�̂�
        img = heatmap*0.5 + original_img # �摜�Əd�˂�
        cv2.imwrite(output_path, img)

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type = bool, default = False, help = 'Train the network or visualize a CAM')
    parser.add_argument("--image_path", type = str, help = "Path of an image to run the network on")
    parser.add_argument("--output_path", type = str, default = "heatmap.jpg", help = "Path of an image to run the network on")
    parser.add_argument("--model_path", type = str, help = "Path of the trained model")
    parser.add_argument("--dataset_path", type = str, help = \
        'Path to image dataset. Should have pos/neg folders, like in the inria person dataset. \
        http://pascal.inrialpes.fr/data/human/')
    args = parser.parse_args()
    return args

if __name__ == '__main__':
	args = get_args()
        if args.train:
                train(args.dataset_path)
        else:
                visualize_class_activation_map(args.model_path, args.image_path, args.output_path)
