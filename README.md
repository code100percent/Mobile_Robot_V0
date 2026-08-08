# Mobile_Manipulation_Robot_V0


building docker image
docker build -t l2-slam:humble 
docker run -it \
  --network host \
  --name l2_run \
  l2-slam:humble

Problems and solutions :
buffer overflow to docker latency solved :
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.rmem_default=26214400
