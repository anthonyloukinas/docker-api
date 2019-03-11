from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import docker
from docker.errors import APIError, ImageNotFound, ContainerError, NotFound, InvalidVersion

app = Flask(__name__)
api = Api(app)

class Client():
    def init(this):
        client = docker.from_env()
        # Checks if server is responive (Have not tested the error. Not sure what we should do here.)
        try:
            status = client.ping()
            return client
        except APIError:
            pass


# Containers
class CreateContainer(Resource):
    def put(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Name of the container')
        parser.add_argument('Image', type=str, required=True, help='Container image')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            container = client.containers.run(image=args.Image, name=args.Name, detach=True)
            return {"Id": container.id}, 200
        except ContainerError:
            return {"message": "Container exited with a non-zero exit code"}, 500
        except ImageNotFound:
            print(ImageNotFound)
            return {"message": "Specified image does not exist"}, 500
        except APIError:
            return {"message": "Server error"}, 500

class GetContainer(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Container name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            container = client.containers.get(container_id=args.Name)
            return container.attrs, 200
        except NotFound:
            return {"message": "Container does not exist"}, 200
        except APIError:
            return {"message": "Server error"}, 500

class StopContainer(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Container name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            container = client.containers.get(container_id=args.Name)
            print(container.status)
            if(container.status == 'exited'):
                return {"message": "{} is already in stopped state".format(container.short_id)}
            elif(container.status == 'running'):
                container.stop()
                return {"message": "{} has been stopped".format(container.short_id)}
            else:
                return {"message": "{} is already in {} state".format(container.short_id, container.status)}
        except APIError:
            return {"message": "Server error"}, 500


# Services
class CreateService(Resource):
    def put(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Image', type=str, required=True, help='Container image')
        parser.add_argument('Name', type=str, required=True, help='Service name')
        parser.add_argument('Replicas', type=int, required=True, help='Container replicas')
        parser.add_argument('Resources', type=dict, required=True, help='Container resource limits')
        parser.add_argument('Container_Labels', type=dict, required=False, help='Container labels')
        parser.add_argument('Service_Labels', type=dict, required=False, help='Service labels')
        parser.add_argument('Endpoint_Spec', type=dict, required=False, help='Endpoint spec')
        args = parser.parse_args(strict=True)

        print(args.Endpoint_Spec)

        client = Client().init()

        try:
            service = client.services.create(
                image=args.Image,
                command=None,
                name=args.Name,
                container_labels=args.Container_Labels,
                mode=docker.types.ServiceMode(mode="replicated", replicas=args.Replicas),
                resources=docker.types.Resources(cpu_limit=args.Resources['cpu_limit'], mem_limit=args.Resources['mem_limit']),
                endpoint_spec=docker.types.EndpointSpec(mode='vip', ports={80: 80}),
                labels=args.Service_Labels
                )
            return {"Id": service.short_id}, 200
        except APIError:
            return {"message": "Server error"}, 500

class RemoveService(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Service name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            service = client.services.get(service_id=args.Name)
            service.remove()
            return {"message": "{} has been removed".format(service.short_id)}, 200
        except APIError:
            return {"message": "Server error"}, 500

class GetService(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Service name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            service = client.services.get(service_id=args.Name)
            return service.attrs, 200
        except NotFound:
            return {"message": "Service does not exist"}, 200
        except APIError:
            return {"message": "Server error"}, 500
        except InvalidVersion:
            return {"message": "One or more arugments is not supported with the current API version"}, 500

class ScaleService(Resource):
    def put(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Service name or id')
        parser.add_argument('Replicas', type=int, required=True, help='Scale services to this amount of replicas')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            service = client.services.get(service_id=args.Name)
            service.scale(args.Replicas)
            return {"message": "{} has been scaled to {} replicas".format(args.Name, args.Replicas)}
        except:
            return {"message": "Server error"} # need to error handle more here

class GetServiceTasks(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Service name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            service = client.services.get(service_id=args.Name)
            return service.tasks(), 200
        except APIError:
            return {"message": "Server error"}, 500


# Volumes
class CreateVolume(Resource):
    def put(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=False, help='Volume name or id')
        parser.add_argument('Driver', type=str, required=False, help='Volume driver')
        parser.add_argument('Labels', type=dict, required=False, help='Volume labels')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            volume = client.volumes.create(name=args.Name, driver=args.Driver, labels=args.Labels)
            return {"message": "{} volume has been created".format(volume.short_id)}, 200
        except APIError:
            return {"message": "Server error"}, 500

class GetVolume(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Volume name or id')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            volume = client.volumes.get(volume_id=args.Name)
            return volume.attrs, 200
        except NotFound:
            return {"message": "Volume does not exist"}, 200
        except APIError:
            return {"message": "Server erroer"}, 500

class RemoveVolume(Resource):
    def get(this):
        parser = reqparse.RequestParser()
        parser.add_argument('Name', type=str, required=True, help='Volume name or id')
        parser.add_argument('Force', type=bool, required=False, help='Force volume to be removed true/false')
        args = parser.parse_args(strict=True)

        client = Client().init()

        try:
            volume = client.volumes.get(volume_id=args.Name)
            volume.remove(force=args.Force)
            return {"message": "{} volume has been removed".format(args.Name)}, 200
        except NotFound:
            return {"message": "Volume does not exist"}, 200
        except APIError:
            return {"message": "Server error"}, 500

class ListVolumes(Resource): # Not working atm, need to figure out for loops in Python again.
    def get(this):
        client = Client().init()

        try:
            volumeArr = []
            volumes = client.volumes.list()

            return volumeArr, 200
        except APIError:
            return {"message": "Server error"}, 500

# Containers
api.add_resource(CreateContainer, '/api/v1/create_container')
api.add_resource(GetContainer, '/api/v1/get_container')
api.add_resource(StopContainer, '/api/v1/stop_container')

# Services
api.add_resource(GetService, '/api/v1/get_service')
api.add_resource(CreateService, '/api/v1/create_service')
api.add_resource(RemoveService, '/api/v1/remove_service')
api.add_resource(ScaleService, '/api/v1/scale_service')
api.add_resource(GetServiceTasks, '/api/v1/get_service_tasks')
# Need to add an update service function

# Volumes
api.add_resource(GetVolume, '/api/v1/volumes/get_volume')
api.add_resource(RemoveVolume, '/api/v1/volumes/remove_volume')
api.add_resource(CreateVolume, '/api/v1/volumes/create_volume')

if __name__ == '__main__':
    app.run(debug=True)