#!/usr/bin/env python
# -*- coding: utf-8 -*-

from keras.models import *
from keras.callbacks import *
import keras.backend as K
from model import *
from data import *
import cv2
import argparse

# トレーニング
def train(dataset_path):
        # モデル取得
        model = get_model()
        
        # データセット取得
        X, y = load_inria_person(dataset_path)
        
        print("Training..")
        
        # 途中のセーブ方法を指定
        checkpoint_path="weights.{epoch:02d}-{val_loss:.2f}.hdf5"
        checkpoint = ModelCheckpoint(checkpoint_path, monitor='val_loss', verbose=0, save_best_only=False, save_weights_only=False, mode='auto')
        
        # 学習スタート
        model.fit(X, y, nb_epoch=40, batch_size=32, validation_split=0.2, verbose=1, callbacks=[checkpoint])

# 可視化
def visualize_class_activation_map(model_path, img_path, output_path):
        # モデルのロード
        model = load_model(model_path)
        
        # 対象画像の読込み
        original_img = cv2.imread(img_path, 1)
        width, height, _ = original_img.shape

        # リシェイプ
        #Reshape to the network input shape (3, w, h).
        img = np.array([np.transpose(np.float32(original_img), (2, 0, 1))])
        
        #Get the 512 input weights to the softmax.
        class_weights = model.layers[-1].get_weights()[0]     # [CAM] えーと？？？
        final_conv_layer = get_output_layer(model, "conv5_3") # [CAM] えーと？？？
        get_output = K.function([model.layers[0].input], [final_conv_layer.output, model.layers[-1].output]) # [CAM] えーと？？？
        
        # https://keras.io/ja/getting-started/faq/
        [conv_outputs, predictions] = get_output([img]) # 画像を入力!
        conv_outputs = conv_outputs[0, :, :, :]         # [CAM] えーと？？？

        # CAMの生成
        # Create the class activation map.
        
        # ゼロクリア
        cam = np.zeros(dtype = np.float32, shape = conv_outputs.shape[1:3]) 
        
        for i, w in enumerate(class_weights[:, 1]): # [CAM] えーと？？？
                cam += w * conv_outputs[i, :, :]    # [CAM] えーと？？？

        print("predictions", predictions)
        cam /= np.max(cam)                      # 最大値で正規化
        cam = cv2.resize(cam, (height, width))  # opencvでnumpyをリサイズ
        
        heatmap = cv2.applyColorMap(np.uint8(255*cam), cv2.COLORMAP_JET) # ヒートマップ。便利！
        heatmap[np.where(cam < 0.2)] = 0 # 0.2より小を切り捨て
        img = heatmap*0.5 + original_img # 画像と重ねる
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
    if(args.train):
        train(args.dataset_path)
    else:
        visualize_class_activation_map(args.model_path, args.image_path, args.output_path)
