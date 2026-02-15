The easiest way to run a Docker image in the cloud
author
Yiren Lu@YirenLu
Solutions Engineer
Docker has revolutionized the way developers build, package, and distribute applications. By containerizing an application, you ensure that it runs consistently across different environments, reducing the “works on my machine” problem. But while running a Docker image locally is straightforward (you can use Docker Desktop or Docker Engine), deploying and managing it in the cloud introduces complexities — networking, scaling, and infrastructure overhead, to name a few.

This is where Modal comes in.

Modal is a Python library that lets you run code in containers in the cloud - and it’s the easiest way to run a Docker image in the cloud.

Modal allows you to specify custom images for those containers, including images from public registries like Docker Hub as well as private images from AWS ECR and GCP Artifact Registry.

In this guide, we’ll cover how you can run both public and private images, as well as images defined in a Dockerfile, on Modal, in less than five minutes.

Why use Modal to run Docker images?
Modal provides the fastest, easiest, and most developer-friendly way to run Docker containers in the cloud. Here’s why it stands out:

✅ No infrastructure management
With Modal, you don’t need to provision VMs, manage Kubernetes clusters, or worry about networking. Just define your container, and Modal handles the rest.

✅ Automatic scaling
Modal seamlessly scales your workloads up or down based on demand, eliminating the need for manual tuning or auto-scaling configurations.

✅ Simple API integration
Unlike traditional cloud providers that require complex CLI tools and configurations, Modal lets you run Docker images using a simple Python-based API.

✅ Cost efficiency
Modal only charges for compute time, so your containers shut down when they’re not in use—perfect for intermittent workloads like batch jobs or model inference.

Prerequisites
To run a Docker image on Modal, you will need to:

Create an account at modal.com
Run pip install modal to install the modal Python package
Run modal setup to authenticate (if this doesn’t work, try python -m modal setup)
Copy the code below into a file called app.py
Run modal deploy app.py to deploy your function
Running an arbitrary public image
Public registries like Docker Hub have many pre-built container images for common software packages. You can specify public images for your Modal function using Image.from_registry.

In the example below, we run an official CUDA image from Docker Hub that is a requirement for running cupy, a CUDA replacement for numpy.

import modal

# 1) use officially supported CUDA image
# 2) pip install cupy, a CUDA replacement for numpy
image = modal.Image.from_registry("nvidia/cuda:12.4.0-devel-ubuntu22.04", add_python="3.11").pip_install("cupy-cuda12x")

app = modal.App("example-gpu", image=image)


@app.function(gpu="A10G")  # 3) attach a GPU to your function
def square(x=2):
    import cupy as cp

    print(f"The square of {x} is {cp.square(x)}")

Copy
Running a private registry image
Private Docker Hub, AWS ECR, and GCP Artifact Registry images are also supported.

Running a custom Docker image from a Dockerfile
Sometimes, you might be working in a setting where the environment is already defined as a container image in the form of a Dockerfile. Modal supports defining a container image directly from a Dockerfile via the Image.from_dockerfile function. It takes a path to an existing Dockerfile.

For instance, we might write a Dockerfile based on the official Python image and add scikit-learn:

FROM python:3.11

RUN pip install sklearn

Copy
We can then define a Modal image from this Dockerfile:

import modal

dockerfile_image = modal.Image.from_dockerfile("Dockerfile")

@app.function(image=dockerfile_image)
def fit():
    import sklearn
    ...

Copy
Conclusion
Running a Docker image in the cloud doesn’t have to be complicated. With Modal, you can go from a local containerized app to a fully managed cloud deployment in just a few lines of Python code.

Whether you’re deploying web applications, machine learning models, or batch processing workloads, Modal offers the easiest and most scalable way to run Docker images and more in the cloud.

Try Modal today and simplify your cloud container deployments!