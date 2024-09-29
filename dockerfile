FROM pytorch/pytorch:2.2.2-cuda12.1-cudnn8-devel

ENV DEBIAN_FRONTEND noninteractive

COPY ./req.txt ./req.txt

RUN apt-get update && apt-get install -y git

RUN pip install -r req.txt

COPY . .

EXPOSE 8000

CMD ["python", "-um", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
