import torch
print(torch.cuda.is_available())  # Debe dar True
print(torch.version.cuda)         # Debe decir 12.1