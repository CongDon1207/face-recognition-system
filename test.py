import onnxruntime as ort
print(ort.get_device())
print(ort.get_available_providers())
sess = ort.InferenceSession("your_model.onnx", providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
print(sess.get_providers())