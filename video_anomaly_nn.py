import os

import cv2
import numpy as np
import video_anomaly_service as video_service
from sklearn.utils import shuffle
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPool2D
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dropout
from tensorflow.keras.models import load_model

DOWNLOAD_TRAINING_SET = True
dir_path = os.path.dirname(os.path.realpath(__file__))

video_service.setup()
CONFIG = video_service.get_config()


def download_bucket(DOWNLOAD_TRAINING_SET, bucket_name, xs, label, ys):
    objects = video_service.get_minio_objects(bucket_name)
    print(f"Objects in bucket '{bucket_name}':")
    for obj in objects:
        print(f" - {obj.object_name} (Size: {obj.size} bytes, Last Modified: {obj.last_modified})")
        video_file_path = dir_path + "/"+  CONFIG['temp_folder'] + '/' + obj.object_name + ".mp4"
        if DOWNLOAD_TRAINING_SET == True:
            video_service.download_file(bucket_name, obj.object_name, video_file_path)
        
        vidcap = cv2.VideoCapture(video_file_path)

        count = 0
        while(True):
            ret, frame = vidcap.read()
            print("count " + str(count))    

            if ret == True:
                stretch_near = cv2.resize(frame, (100, 100), interpolation = cv2.INTER_LINEAR)
                
                for i in range(4):
                    stretch_near = cv2.rotate(stretch_near, cv2.ROTATE_90_CLOCKWISE)
                    xs.append(np.array(stretch_near))
                    ys.append(label)
                count += 1 
            else:
                print("count " + str(count) + " xs " + str(len(xs)) + " ys " + str(len(ys)))
                break    

        
xs = []
ys = []
download_bucket(DOWNLOAD_TRAINING_SET, CONFIG["minio_baseline_bucket"], xs, [0,1], ys)
download_bucket(DOWNLOAD_TRAINING_SET, CONFIG["minio_alarm_bucket"], xs, [1,0], ys)
xs = np.array(xs)
xs = xs.astype('float32') / 255.0
ys = np.array(ys)

xs, ys = shuffle(xs, ys, random_state=0)

#print(xs[:5]) 
#print(ys[:5]) 

train_len = int(len(ys)*0.9)
x_train = xs[:train_len]
y_train = ys[:train_len]
x_test = xs[train_len:len(xs)]
y_test = ys[train_len:len(ys)]


in_shape  =(100,100,3)
n_classes = 2
#print(in_shape, n_classes)
#print("xs.shape")
#print(xs.shape)
#print("ys.shape")
#print(ys.shape)
#print("x_train.shape")
#print(x_train.shape)
#print(y_train[:5]) 
#print("y_train.shape")
#print(y_train.shape)
#print("x_test.shape")
#print(x_test.shape)
#print("y_test.shape")
#print(y_test.shape)
#print(x_train[:5]) 

model = Sequential()
model.add(Conv2D(32, (3,3), activation='relu', kernel_initializer='he_uniform', input_shape=in_shape))
model.add(MaxPool2D((2, 2)))
model.add(Flatten())
model.add(Dense(100, activation='relu', kernel_initializer='he_uniform'))
model.add(Dropout(0.5))
model.add(Dense(n_classes, activation='softmax'))
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(x_train, y_train, epochs=1, batch_size=128, verbose=1)

loss, acc = model.evaluate(x_test, y_test)
print('Accuracy: %.3f' % acc)
print('loss: %.3f' % loss)


model.save(CONFIG['assets_folder'] + '/cnn_model.h5')
yhats = model.predict(xs)
guessed = 0
for i in range(len(yhats)):
    yhat = np.argmax(yhats[i])
    yt = np.argmax(ys[i])
    if yhat == yt:
        guessed = guessed +1 
    #print(str(yhat) + "_" + str(yt))
print("guessed " + str(guessed) + " tot " + str(len(yhats)))   




