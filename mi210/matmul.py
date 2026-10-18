import torch

n = torch.cuda.device_count()  # ROCm shows up as torch.cuda
print(n, "GPU(s):", [torch.cuda.get_device_name(i) for i in range(n)])
for i in range(n):
    a = torch.randn(4096, 4096, device=f"cuda:{i}")
    print(i, (a @ a).sum().item())
