import ttnn

d = ttnn.open_device(device_id=0)
a = ttnn.ones((64, 64), dtype=ttnn.bfloat16, layout=ttnn.TILE_LAYOUT, device=d)
print("matmul:", ttnn.from_device(ttnn.matmul(a, a)).to_list()[0][:4])
ttnn.close_device(d)
