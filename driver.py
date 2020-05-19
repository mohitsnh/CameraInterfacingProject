from thorlabs import ThorlabsDCx
import matplotlib.pyplot as plt
import time
cam = ThorlabsDCx()
#cam.open()

print(cam.get_roi())
for i in range(25):
	test = cam.acquire_image_data()
	print(test)
	print(test.shape)
	#cam.save_image();
	fig = plt.figure(figsize=(6, 3.2))
	ax = fig.add_subplot(111)
	ax.set_title('colorMap')
	plt.imshow(test)
	ax.set_aspect('equal')
	cax = fig.add_axes([0.12, 0.1, 0.78, 0.8])
	cax.get_xaxis().set_visible(False)
	cax.get_yaxis().set_visible(False)
	cax.patch.set_alpha(0)
	cax.set_frame_on(False)
	plt.colorbar(orientation='vertical')
	plt.ion()
	plt.show()
	time.sleep(5)
	plt.close(fig)
cam.close()