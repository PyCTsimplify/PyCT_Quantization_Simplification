import keras
from dnnct.myDNN import NNModel 
from dnnct.tnnDNN import NNModel as tnnNNModel
import itertools
import numpy as np


myModel = None
def init_model(model_path,model_type="qnn",delta_factor=0.75):
	global myModel
	model = keras.models.load_model(model_path)
	# print(model.summary())
	layers = [l for l in model.layers if type(l).__name__ not in ['InputLayer','Embedding','Dropout']]
	if model_type == "cnn":
		myModel = NNModel()
	elif model_type == "qnn":
		myModel = tnnNNModel(delta_factor=delta_factor)

	# 1: is because 1st dim of input shape of Keras model is batch size (None)
	myModel.input_shape = model.input_shape[1:]
	for layer in layers:
		myModel.addLayer(layer)


def predict(**data):
	input_shape = myModel.input_shape
	iter_args = (range(dim) for dim in input_shape)
	X = np.zeros(input_shape).tolist()
	data_name_prefix = "v_"
	for i in itertools.product(*iter_args):
		if len(i) == 2:
			X[i[0]][i[1]] = data[f"{data_name_prefix}{i[0]}_{i[1]}"]
		elif len(i) == 3:
			X[i[0]][i[1]][i[2]] = data[f"{data_name_prefix}{i[0]}_{i[1]}_{i[2]}"]
		elif len(i) == 4:
			X[i[0]][i[1]][i[2]][i[3]] = data[f"{data_name_prefix}{i[0]}_{i[1]}_{i[2]}_{i[3]}"]

	out_val = myModel.forward(X)
	if len(out_val) == 1:
		if isinstance(out_val[0],list):
			if out_val[0][0] > 0.5:
				ret_class = 1
			else:
				ret_class = 0
		else:
			if out_val[0] > 0.5:
				ret_class = 1
			else:
				ret_class = 0
	else:
		max_val, ret_class = out_val[0], 0
		for i,cl_val in enumerate(out_val):
			if cl_val > max_val:
				max_val, ret_class = cl_val, i

	print("[DEBUG]predicted class:", ret_class)
	return ret_class