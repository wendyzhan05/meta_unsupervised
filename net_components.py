import torch
import torch.nn as nn
import torchvision.datasets as dsets
import torchvision.transforms as transforms
from torch.autograd import Variable


# Template for Bias and Weight Update Metalearner
# inputs in order v_i, w_ij, v_j
class Meta(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(Meta, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return out


# Template for Single Structure
class SingleNet(nn.Module):

    def __init__(self, input_size, hidden1, hidden2, output_size, meta_weight):
        super(SingleNet, self).__init__()
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(input_size, hidden1)
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.fc3 = nn.Linear(hidden2, output_size)
        self.impulse = []
        self.add_module("meta_weight", meta_weight)

    # get new weight
    def get_update(self, v_i, w_ij, v_j):
        inputs = Variable(torch.Tensor([v_i, w_ij, v_j]), requires_grad=True)
        print("break")
        return self.meta_weight.forward(inputs).data[0]

    # compute output and propagate Hebbian updates
    def forward(self, x):
        print(type(x))
        out = x
        self.impulse = []
        self.impulse.append(out)
        out = self.fc1(out)
        out = self.relu(out)
        self.impulse.append(out)
        out = self.fc2(out)
        out = self.relu(out)
        self.impulse.append(out)
        out = self.fc3(out)
        out = self.relu(out)
        self.impulse.append(out)
        param_state = self.state_dict(keep_vars=True)
        keys = list(param_state.keys())

        def is_weight_param(param):
            return (".weight" in param) and ("meta" not in param)

        weight_params = [key for key in keys if is_weight_param(key)]
        # print(weight_params)
        if len(weight_params) != len(self.impulse) - 1:
            print("Keys:" + str(len(keys)))
            print(keys)
            print("Impulse:" + str(len(self.impulse)))
            print(self.impulse)
            raise ValueError("Num keys not 1 less than num impulses")
        for i in range(0, len(weight_params)):
            layer = param_state[weight_params[i]]
            # print(layer)
            input_layer = self.impulse[i]
            output_layer = self.impulse[i + 1]
            for input_index in range(0, len(input_layer)):
                for output_index in range(0, len(output_layer)):
                    # print(input_layer.data)
                    input_to_neuron = input_layer.data[0, input_index]
                    # print(input_to_neuron)
                    output_from_neuron = output_layer.data[0, output_index]
                    # print(output_from_neuron)
                    neuron_weight = layer.data[output_index, input_index]
                    # print(neuron_weight)
                    new_weight = self.get_update(input_to_neuron, neuron_weight, output_from_neuron)
                    # print(new_weight)
                    layer.data[output_index, input_index] = new_weight
                    # print(new_weight - neuron_weight)
                    # print(type(new_weight - neuron_weight))
        print("finished a forward pass")
        print(self.meta_weight.state_dict())
        return out
