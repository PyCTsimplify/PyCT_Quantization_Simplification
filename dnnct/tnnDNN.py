import sys
import numpy as np
import math
from itertools import product
import collections.abc
from functools import reduce  
import logging

from keras.layers import (
    Dense,
    Conv1D, Conv2D,
    LocallyConnected1D, LocallyConnected2D,
    Flatten,
    ELU,
    Activation,
    MaxPool2D,
    LSTM,
    Embedding,
    BatchNormalization,
    SimpleRNN,
    MultiHeadAttention,
    GlobalAveragePooling1D
)

LAYERS = (
    Dense,
    Conv1D, Conv2D,
    LocallyConnected1D, LocallyConnected2D,
    Flatten,
    ELU,
    Activation,
    MaxPool2D,
    LSTM,
    Embedding,
    BatchNormalization,
)

ACTIVATIONS = (
    'linear',
    'relu',
    'elu',
    'softplus',
    'softsign',
    'sigmoid',
    'tanh',
    'hard_sigmoid',
    'softmax',
)

debug = False

def concolic_exp(x):
    if x < 0:
        return 1.0 / concolic_exp(-x)
    if x > 1:
        try:
            return concolic_exp(x / 2) ** 2
        except OverflowError:
            print(x, 'OverflowError')   
    a0 = 1.0
    a1 = x        #6737
    a2 = x**2 / 2 #9891
    # a3 = x**3 / 6 #9985
    # a4 = x**4 / 24
    # a5 = x**5 / 120
    # a6 = x**6 / 720
    # a7 = x**7 / 5040
    # a8 = x**8 / 40320
    # a9 = x**9 / 362880

    return a0 + a1 + a2
    # return a0 + a1 + a2 + a3 + a4 + a5 + a6 + a7 + a8 + a9

def my_exp_complex(x):
    if x < 0:
        return 1.0 / my_exp(-x)
    elif x > 1:
        return my_exp(x/2) * my_exp(x/2)
    elif (math.exp(x) >= x + 1) and (math.exp(x) <= 2*x + 1):
        try:
            return math.exp(x)
        except mathexpError:
            print(x, 'math.expError')
def my_exp(x):
    if x < -15:
        return 0.0
    return math.exp(x)
    if x < 0:
        return 1.0 / my_exp(-x)
    else:
        try:
            return math.exp(x)
        except OverflowError:
            print(x, 'OverflowError')
            return sys.float_info.max


# exp_func = math.exp
exp_func = my_exp

def act_tanh(x):
    if x == 0:
        return 0.0
    elif x >= 3:
        return 1.0
    elif x <= -3:
        return -1.0
    elif x < 0:
        return -act_tanh(-x)
    else:
        # exp_x = my_exp(x)
        # exp_minus_x = my_exp(-x)
        exp_x = exp_func(x)
        exp_minus_x = exp_func(-x)
        return (exp_x - exp_minus_x) / (exp_x + exp_minus_x)

def act_sigmoid(x):
    # return 1.0 / (1.0 + concolic_exp(-x))
    if x == 0:
        return 0.5
    elif x >= 5:
        return 1.0
    elif x <= -5:
        return 0.0
    else:
        # return 1.0 / (1.0 + my_exp(-x))
        return 1.0 / (1.0 + exp_func(-x))

def act_softmax(x):
    # exp_values = [concolic_exp(val) for val in x]    # 計算指數函數
    max_val = x[0]
    for val in x:
        if val > max_val:
            max_val = val
    exp_values = [exp_func(val - max_val) for val in x]    # 計算指數函數
    softmax_values = [val / sum(exp_values) for val in exp_values]    # 計算softmax值
    return softmax_values

# https://stackoverflow.com/questions/17531796/find-the-dimensions-of-a-multidimensional-python-array
# return the dimension of a python list
def dim(a):
    if not type(a) == list:
        return []
    return [len(a)] + dim(a[0])


# acivation function
def actFunc(val, type):
    if type=='linear':
        return val
    elif type=='relu':
        if val < 0.0:
            return 0.0
        else:
            return val
    elif type=='softmax':
        return act_softmax(val)
    elif type=='sigmoid':
        return act_sigmoid(val)
    elif type=='tanh':
        return act_tanh(val)
    elif type=='elu':
        pass
    elif type=='softplus':
        pass
    elif type=='softsign':
        pass
    else:
        raise NotImplementedError()
    return 0


class ActivationLayer:
    def __init__(self, type):
        if type not in ACTIVATIONS: raise NotImplementedError()
        self.type = type
        self._output = None
    def forward(self, tensor_in):
        out_shape = dim(tensor_in)
        tensor_out = tensor_in
        if len(out_shape)==1:
            # print('start 1: ', self.type, tensor_in)
            if self.type=="softmax":
                # print('start 1-0 softmax')
                tensor_out = act_softmax(tensor_in)
                # raise NotImplementedError()
                # denom = 0
                # for idx in range(0, out_shape[0]):
                #     denom = denom + math.exp(tensor_in[idx])
                # for idx in range(0, out_shape[0]):
                #     tensor_out[idx] = math.exp(tensor_in[idx]) / denom
            else:
                # print('start 1-0')
                for idx in range(0, out_shape[0]):
                    # print('start 1-', idx, tensor_in[idx])
                    tensor_out[idx] = actFunc(tensor_in[idx], self.type)
                    # print('end 1-', tensor_out[idx])
            # print('end 1')
        elif len(out_shape)==2:
            # print('start 2')
            for i, j in product( range(0, out_shape[0]),
                                 range(0, out_shape[1])):
                tensor_out[i][j] = actFunc(tensor_in[i][j], self.type)
            # print('end 2')
        elif len(out_shape)==3:
            # print('start 3')
            for i, j, k in product( range(0, out_shape[0]),
                                    range(0, out_shape[1]),
                                    range(0, out_shape[2])):
                tensor_out[i][j][k] = actFunc(tensor_in[i][j][k], self.type)
            # print('end 3')
        else:
            raise NotImplementedError()
        # print('end all')
        if debug:
            print("[DEBUG]Finish Activation Layer forwarding!!")

        #print("Output #Activations=%i" % len(tensor_out))
        ## DEBUG
        self._output = tensor_out
        #print(tensor_in)
        #print(tensor_out)
        return tensor_out
    def getOutput(self):
        return self._output

class DenseLayer:
    def __init__(self, weights, bias, shape, activation="None",delta_factor=0.75):
        self.weights = weights.astype(float)
        self.bias = bias
        self.shape = shape
        self.activation = activation
        self._output = None
        self.delta_factor = delta_factor
        self._delta = self.delta()
    def delta(self):
        """Calculate delta based on weights."""
        n = self.weights.size
        delta = (self.delta_factor / n)* np.sum(np.abs(self.weights))
        return delta
    def addActivation(self, activation):
        self.activation = activation

    def forward(self, tensor_in):
        in_shape = dim(tensor_in)
        assert len(in_shape)==1, "DenseLayer.forward() with non flattened input!"
        assert in_shape[0]==self.shape[1], "DenseLayer.forward(), dim. mismatching between input and weights!"
        tensor_out = self.bias.tolist()

        for out_id in range(0, self.shape[0]):
            ## Dot operation
            for in_id in range(0, self.shape[1]):
                # Adjust input according to weight
                if self.weights[out_id][in_id] > self._delta:
                    adjusted_input = tensor_in[in_id]
                elif abs(self.weights[out_id][in_id]) <= self._delta:
                    adjusted_input = 0
                else:
                    adjusted_input = -tensor_in[in_id]

                tensor_out[out_id] = adjusted_input+ tensor_out[out_id]
            if self.activation!="None":
                tensor_out[out_id] = actFunc(tensor_out[out_id], self.activation)

        if debug:
            print("[DEBUG]Finish Dense Layer forwarding!!")

        #print("Output #Activations=%i" % len(tensor_out))
        self._output = tensor_out
        return tensor_out

    def getOutput(self):
        return self._output


class Conv2DLayer:
    def __init__(self, weights, bias, shape, activation="None", stride=1, padding='valid',delta_factor=0.75):
        self.weights = weights.astype(float)
        self.shape = shape
        self.bias = bias
        self.padding = padding
        self.stride = stride
        self.activation = activation
        self._output = None
        self.delta_factor = delta_factor
        self._delta = self.delta()
    def delta(self):
        """Calculate delta based on weights."""
        n = self.weights.size
        delta = (self.delta_factor / n) * np.sum(np.abs(self.weights))
        return delta
    def addActivation(self, activation):
        self.activation = activation
    def forward(self, tensor_in):
        in_shape = dim(tensor_in)
        assert in_shape[2] == self.shape[3], "Conv2DLayer, channel length mismatching!"
        out_shape = [in_shape[0]-self.shape[1]+1,
                     in_shape[1]-self.shape[2]+1,
                     self.shape[0]]
        #tensor_out = np.zeros( out_shape ).tolist()
        tensor_out = []

        for _ in range(out_shape[0]):
            tensor_out.append( [[0.0]*out_shape[2] for i in range(out_shape[1])] ) 

        for channel in range(0, out_shape[2]):
                filter_weights = self.weights[channel]
                num_row, num_col, num_depth = self.shape[1], self.shape[2], self.shape[3]
                for row in range(0, out_shape[0]):
                    for col in range(0, out_shape[1]):
                        tensor_out[row][col][channel] = float(self.bias[channel])


                        for i, j, k in product( range(row, row+num_row),
                                                range(col, col+num_col),
                                                range(0, num_depth)):
                            weight = float(filter_weights[i-row][j-col][k])
                            if weight > self._delta:
                                input_value = tensor_in[i][j][k]
                            elif abs(weight)<=self._delta:
                                input_value = 0
                            else:
                                input_value = -tensor_in[i][j][k]
                            tensor_out[row][col][channel] += input_value

                        if self.activation!="None":
                            tensor_out[row][col][channel] = actFunc(tensor_out[row][col][channel], self.activation)

                    #print(type(tensor_out[row][col][channel]))
            #print("Finished %i feature Map" % channel)
        
        if debug:
            print("[DEBUG]Finish Conv2D Layer forwarding!!")

        #print("Feature Map Shape: %ix%ix%i" % tuple(out_shape))
        self._output = tensor_out
        return tensor_out

    def getOutput(self):
        return self._output


class MaxPool2DLayer:
    def __init__(self, shape, stride=1, padding='valid'):
        self.pool_size = shape
        self.stride = stride
        self.padding = padding
        self._output = None
    def forward(self, tensor_in):
        in_shape = dim(tensor_in)
        assert(len(in_shape)==3)

        ## For now, we assume stride=1 and padding='valid'
        ## TODO  stride!=1 and padding!='valid'
        r, c = self.pool_size[0], self.pool_size[1]
        out_shape = [ in_shape[0] // r,
                      in_shape[1] // c,
                      in_shape[2]]
        # tensor_out = np.zeros(out_shape).tolist()
        tensor_out = []
        for _ in range(out_shape[0]):
            tensor_out.append( [[0.0]*out_shape[2] for i in range(out_shape[1])] )

        for row in range(0, out_shape[0]):
            for col in range(0, out_shape[1]):
                for depth in range(0, out_shape[2]):
                    max_val = -10000
                    if tensor_in[row*r  ][col*c  ][depth] > max_val:
                        max_val = tensor_in[row*r  ][col*c  ][depth]
                    if tensor_in[row*r+1][col*c  ][depth] > max_val:
                        max_val = tensor_in[row*r+1][col*c  ][depth]
                    if tensor_in[row*r  ][col*c+1][depth] > max_val:
                        max_val = tensor_in[row*r  ][col*c+1][depth]
                    if tensor_in[row*r+1][col*c+1][depth] > max_val:
                        max_val = tensor_in[row*r+1][col*c+1][depth]
                    tensor_out[row][col][depth] = max_val
                    #print(type(tensor_out[row][col][depth]))
        ## fix the shape of tensor_out

        if debug:
            print("[DEBUG]Finish MaxPool2D Layer forwarding!!")

        #print("Feature Map Shape: %ix%ix%i" % tuple(out_shape))
        self._output = tensor_out
        return tensor_out

    def getOutput(self):
        return self._output


class FlattenLayer:
    def __init__(self):
        self._output = None
    def forward(self, tensor_in):
        tensor_out = self._flatten(tensor_in)
        self._output = tensor_out
        return tensor_out
    def _flatten(self, x):
        if isinstance(x, collections.Iterable):
            return [a for i in x for a in self._flatten(i)]
        else:
            return [x]
    def getOutput(self):
        return self._output


# Define SimpleRNN class
class SimpleRNNLayer:
    def __init__(self, input_dim, weights, activation='tanh'):        
        self.input_dim = input_dim
        assert activation in (None, "tanh", "linear")
        self.activation = activation
        self.units = weights[0].shape[1]

        self.w_xh, self.w_hh, self.b_h = (w.tolist() for w in weights)

        # Initialize weights
#         self.w_hh = [[0 for i in range(units)] for j in range(units)]
#         self.w_xh = [[0 for i in range(units)] for j in range(input_shape)]
        
        # Initialize biases
#         self.b_h = [0 for i in range(units)]
        
        # Initialize hidden state
        self.h = [0 for i in range(self.units)]
        self._output = None
        
    def call(self, x):
        # Update hidden state
        curr_h = self.h.copy()
        for i in range(self.units):            
            h_i = 0
            for j in range(self.units):
                h_i += curr_h[j] * self.w_hh[j][i]
                
            for j in range(self.input_dim):
                h_i += x[j] * self.w_xh[j][i]
                
            h_i += self.b_h[i]

            if self.activation == 'tanh':
                self.h[i] = act_tanh(h_i)
            else:
                self.h[i] = h_i
        
        # Return hidden state
        return self.h
    
    def init_state(self):
        self.h = [0 for i in range(self.units)]
    
    def forward(self, X):
        self.init_state()
        for i in range(len(X)):
            output_h = self.call(X[i])
        self._output = output_h

        if debug:
            print("[DEBUG]Finish SimpleRNN Layer forwarding!!")

        return output_h

    def getOutput(self):
        return self._output


class LSTMLayer:
    def __init__(self, input_size, weights, delta_factor=0.75):
        self.input_size = input_size   
        self.delta_factor = delta_factor             
        W, U, b = (w for w in weights)
        self.hidden_size = int(W.shape[1] / 4)
       
        # load weights and calculate deltas
        self.W_i, self.delta_W_i = self.load_weights(W[:, :self.hidden_size])
        self.W_f, self.delta_W_f = self.load_weights(W[:, self.hidden_size: self.hidden_size * 2])
        self.W_c, self.delta_W_c = self.load_weights(W[:, self.hidden_size * 2: self.hidden_size * 3])
        self.W_o, self.delta_W_o = self.load_weights(W[:, self.hidden_size * 3:])
       
        self.U_i, self.delta_U_i = self.load_weights(U[:, :self.hidden_size])
        self.U_f, self.delta_U_f = self.load_weights(U[:, self.hidden_size: self.hidden_size * 2])
        self.U_c, self.delta_U_c = self.load_weights(U[:, self.hidden_size * 2: self.hidden_size * 3])
        self.U_o, self.delta_U_o = self.load_weights(U[:, self.hidden_size * 3:])
       
        # load biases
        self.b_i = b[:self.hidden_size].tolist()
        self.b_f = b[self.hidden_size: self.hidden_size * 2].tolist()
        self.b_c = b[self.hidden_size * 2: self.hidden_size * 3].tolist()
        self.b_o = b[self.hidden_size * 3:].tolist()


    def load_weights(self, weights):
        weights = weights.tolist()
        delta = (self.delta_factor / np.size(weights)) * np.sum(np.abs(weights))
        return weights, delta
       
    def forward(self, X):
        # init states
        h0 = np.zeros(self.hidden_size).astype('float32').tolist()
        c0 = np.zeros(self.hidden_size).astype('float32').tolist()
       
        for i in range(len(X)):
            h0, c0 = self.step(X[i], h0, c0)
           
        return h0
       
    def step(self, x, h, c):                
        i = [0.0] * self.hidden_size
        f = [0.0] * self.hidden_size
        o = [0.0] * self.hidden_size
        g = [0.0] * self.hidden_size
       
        for j in range(self.hidden_size):
            for k in range(self.input_size):
                i[j] += self.adjusted_input(x[k], self.W_i[k][j], self.delta_W_i)
                f[j] += self.adjusted_input(x[k], self.W_f[k][j], self.delta_W_f)
                o[j] += self.adjusted_input(x[k], self.W_o[k][j], self.delta_W_o)
                g[j] += self.adjusted_input(x[k], self.W_c[k][j], self.delta_W_c)


            for l in range(self.hidden_size):
                i[j] += self.adjusted_input(h[l], self.U_i[l][j], self.delta_U_i)
                f[j] += self.adjusted_input(h[l], self.U_f[l][j], self.delta_U_f)
                o[j] += self.adjusted_input(h[l], self.U_o[l][j], self.delta_U_o)
                g[j] += self.adjusted_input(h[l], self.U_c[l][j], self.delta_U_c)
       
            i[j] += self.b_i[j]
            f[j] += self.b_f[j]
            o[j] += self.b_o[j]
            g[j] += self.b_c[j]


            i[j] = act_sigmoid(i[j])
            f[j] = act_sigmoid(f[j])
            o[j] = act_sigmoid(o[j])
            g[j] = act_tanh(g[j])


        new_c = [0.0] * self.hidden_size
        new_h = [0.0] * self.hidden_size


        for j in range(self.hidden_size):
            new_c[j] = f[j] * c[j] + i[j] * g[j]
            new_h[j] = o[j] * act_tanh(new_c[j])


        return new_h, new_c


    def adjusted_input(self, input, weight, delta):
        if weight > delta:
            return input
        elif abs(weight) <= delta:
            return 0
        else:
            return -input
    # def adjusted_input(self, input, weight, delta):
    #     if weight > 0:
    #         return input
    #     elif weight <0:
    #         return -input
    #     else:
    #         return 0

class MultiHeadAttentionLayer:
    def __init__(self, num_heads, key_dim_per_heads, wq, bq, wk, bk, wv, bv, output_weights, output_bias,delta_factor=0.75):
        # assert model_dim % num_heads == 0
        self.num_heads = num_heads#20
        self.delta_factor = delta_factor
        # = model_dim #32
        self.key_dim_per_heads = key_dim_per_heads#32
        self.WQ = wq.numpy().tolist()
        self.BQ = bq.numpy().tolist()
        self.WK = wk.numpy().tolist()
        self.BK = bk.numpy().tolist()
        self.WV = wv.numpy().tolist()
        self.BV = bv.numpy().tolist()
        self.WO = output_weights.numpy().tolist()
        self.BO = output_bias.numpy().tolist()        
    def forward(self, input, mask=None):
        if dim(input) == 2:
            return self.forwardSingle(input, mask)
        else:
            return self.forwardBatch(input, mask)
    def adjusted_input(self, input, weight, delta):
        if weight > delta:
            return input
        elif abs(weight) <= delta:
            return 0
        else:
            return -input
    def load_delta(self, weights):
        delta = (self.delta_factor / np.size(weights)) * np.sum(np.abs(weights))
        # aggressive_delta = np.percentile(np.abs(weights), 90)
        # final_delta = max(delta, aggressive_delta)
    
        return delta
    
    def forwardBatch(self, inputs, mask=None):
        return [self.forwardSingle(input, mask) for input in inputs]
    def forwardSingle(self, input, mask=None):
        self.seq_len, self.model_dim = np.array(input).shape
        Q = self.transform_and_split(input, self.WQ, self.BQ)
        K = self.transform_and_split(input, self.WK, self.BK)
        V = self.transform_and_split(input, self.WV, self.BV)#500,20,32
        attentions = [self.dot_product_attention(Q[i], K[i], V[i]) for i in range(self.num_heads)]
        outputs = self.concatenate_and_transform(attentions, self.WO, self.BO)
        return outputs
    
    # def transform_and_split(self,sequence_of_vectors, weights, bias):
    #     outputs = [
    #                     [
    #                         [self.mySum((weights[k][i][j] * vector[k]) for k in range(self.model_dim)) + bias[i][j] for j in range(self.key_dim_per_heads)]#32
    #                         for vector in sequence_of_vectors   #vector:1*32
    #                     ]
    #                     for i in range(self.num_heads)#20
    #                 ]
                
    #     return outputs
    def transform_and_split(self, sequence_of_vectors, weights, bias):
        delta = self.load_delta(weights)
        outputs = [
            [
                [
                    self.mySum(self.adjusted_input(vector[k], weights[k][i][j], delta) for k in range(self.model_dim)) + bias[i][j]
                    for j in range(self.key_dim_per_heads)
                ]
                for vector in sequence_of_vectors
            ]
            for i in range(self.num_heads)
        ]
        return outputs




    def concatenate_and_transform(self,attentions, output_weights, output_bias):
        assert np.array(output_bias).shape == (self.model_dim,)#32
        delta = self.load_delta(output_weights)
        outputs = [
              [
                  self.mySum([
                      self.adjusted_input(attentions[j][word][k], output_weights[j][k][i], delta)
                    #   attentions[j][word][k] * output_weights[j][k][i]
                      for j in range(self.num_heads)
                      for k in range(self.key_dim_per_heads)
                  ]) + output_bias[i]
                  for i in range(self.model_dim)
              ]
              for word in range(self.seq_len)
          ]
        assert np.array(outputs).shape == (self.seq_len, self.model_dim)
        return outputs
    def mySum(self,x):
            s = 0.0
            for i in x:
                s = s + i
            return s
    def dot_product_attention(self, Q, K, V):
        K_T = [*zip(*K)]#32,500
        attention_scores = self.matrix_multiply(Q, K_T)#500,500
        attention_scores = [[score / (self.key_dim_per_heads ** 0.5) for score in attention_score ]for attention_score in attention_scores]#500,500
        attention_scores = self.softmax(attention_scores)#500,500
        context_vector = self.matrix_multiply(attention_scores, V)#500,32
        return context_vector
    def myMax(self,x):
        max = x[0]
        for i in x:
            if i > max:
                max = i
        return max
    def softmax(self,x):
        x_max = [self.myMax(x[i]) for i in range(len(x))]
        e_x = [[my_exp(x[i][j] - x_max[i]) for j in range(len(x[i]))] for i in range(len(x))]
        e_x_sum = [self.mySum(e_x[i]) for i in range(len(e_x))]
        result = [[e_x[i][j] / e_x_sum[i] for j in range(len(e_x[i]))] for i in range(len(e_x)) ]
        return result
    def matrix_multiply(self, matrix1, matrix2):
        if len(matrix1[0]) != len(matrix2):
            raise ValueError("矩陣的維度不符合乘法要求。")

        result = [[0] * len(matrix2[0]) for _ in range(len(matrix1))]

        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                for k in range(len(matrix2)):
                    result[i][j] += matrix1[i][k] * matrix2[k][j]

        return result
    def dot_product(self, vector1, vector2):
        return self.mySum(vector1[i] * vector2[i] for i in range(self.model_dim))

class NNModel:
    def __init__(self,delta_factor=0.75):
        self.layers = []
        self.input_shape = None
        self.delta_factor = delta_factor

    def forward(self, tensor_in):
        # tensor_it = tensor_in
        logging.info("DNN start forwarding")
        for i, layer in enumerate(self.layers):
            tensor_in = layer.forward(tensor_in)
            # print(tensor_in)

        logging.info("DNN finish forwarding")
        return tensor_in

    def getLayOutput(self, idx):
        if idx >= len(self.layers):
            return None
        else:
            return self.layers[idx].getOutput()

    def addLayer(self, layer):

        if type(layer) == Conv2D:
            #print("Conv2D")
            # shape: (outputs, rows, cols, channel)
            weights = layer.get_weights()[0].transpose(3, 0, 1, 2)
            biases = layer.get_weights()[1]
            activation = layer.get_config()['activation']

            self.layers.append(Conv2DLayer(weights, biases, weights.shape, delta_factor=self.delta_factor))
            # print("Add Activation Layer:", activation)
            self.layers.append(ActivationLayer(activation))
        elif type(layer) == Dense:
            #print("Dense")
            # shape: (outputs, inputs)
            weights = layer.get_weights()[0].transpose()
            biases = layer.get_weights()[1]
            activation = layer.get_config()['activation']

            self.layers.append(DenseLayer(weights, biases, weights.shape, delta_factor=self.delta_factor))
            # print("Add Activation Layer:", activation)
            self.layers.append(ActivationLayer(activation))
        elif type(layer) == MaxPool2D:
            #print("MaxPool2D")
            pool_size = layer.get_config()['pool_size']
            # print(pool_size)
            self.layers.append(MaxPool2DLayer(pool_size))
        elif type(layer) == Flatten:
            #print("Flatten")
            self.layers.append(FlattenLayer())
        elif type(layer) == Activation:
            activation = layer.get_config()['activation']
            self.layers.append(ActivationLayer(activation))
        elif type(layer) == SimpleRNN:
            input_dim = layer.input_shape[-1]
            activation = layer.get_config()['activation']
            self.layers.append(SimpleRNNLayer(input_dim, weights=layer.get_weights(), activation=activation))
        elif type(layer) == LSTM:
            input_dim = layer.input_shape[-1]
            self.layers.append(LSTMLayer(input_dim, weights=layer.get_weights(), delta_factor=self.delta_factor))
        elif type(layer)== MultiHeadAttention:
            num_heads = layer.get_config()['num_heads']
            # num_heads#20
            #32*20
            key_dim_per_heads = layer.get_config()['key_dim']
            wq=layer._query_dense.kernel
            bq=layer._query_dense.bias
            wk=layer._key_dense.kernel
            bk=layer._key_dense.bias
            wv=layer._value_dense.kernel
            bv=layer._value_dense.bias
            output_weights=layer._output_dense.kernel
            output_bias=layer._output_dense.bias
            model_dim = layer._output_dense.full_output_shape[-1]
            # print("wq type",type(wq))
            # weights = layer.get_weights()
            # print("weights:",weights)
            # k_weights, q_weights, v_weights = weights[:3]
            # print("q weights shape:", wq.shape)
            # print("q bias shape:", bq.shape)
            # print("q weights shape:", q_weights.shape)
            # print("v weights shape:", v_weights.shape)
            # self.layers.append(MultiHeadAttentionLayer(num_heads, model_dim))
            self.layers.append(MultiHeadAttentionLayer(num_heads, key_dim_per_heads, wq, bq, wk, bk, wv, bv, output_weights, output_bias, delta_factor=self.delta_factor))
        else:
            print(f"Unsupported layer type: {type(layer)}")
            raise NotImplementedError(f"Support for layer type {type(layer)} is not implemented")
