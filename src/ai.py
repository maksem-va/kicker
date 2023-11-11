import tensorflow as tf
from tensorflow.keras import layers, models

class NeuralNetwork:
    def __init__(self, input_size, output_size):
        self.model = self.build_model(input_size, output_size)

    def build_model(self, input_size, output_size):
        model = models.Sequential()
        model.add(layers.Dense(64, activation='relu', input_shape=(input_size,)))
        model.add(layers.Dense(output_size, activation='softmax'))
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    def train(self, features, labels, epochs=10):
        self.model.fit(features, labels, epochs=epochs)

    def predict(self, features):
        return self.model.predict(features)
