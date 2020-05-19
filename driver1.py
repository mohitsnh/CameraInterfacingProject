from thorlabs import ThorlabsDCx

import matplotlib.pyplot as plt
import time
cam = ThorlabsDCx()
#cam.open()
cam.set_roi_pos([0,0])
roi=[40,32]
cam.set_roi_shape(roi)
print("The ROI is set to:" ,roi)
start=time.time()
for i in range(200):
	test = cam.acquire_image_data()
	#print(test)
	#print(test.shape)
end=time.time()
frame_rate=200.0/(end-start)
print("The frame rate is",frame_rate," per second")
cam.close()

