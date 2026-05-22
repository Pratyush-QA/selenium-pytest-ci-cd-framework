# Jenkins Image Builder Notes

These folders are the Python project version of the instructor's Java image-builder examples.

Instructor project flow:

```text
mvn clean package -DskipTests
       -> docker build
       -> docker login
       -> docker push
```

Your Python project flow:

```text
validate Python Selenium Dockerfile
       -> docker build
       -> docker login
       -> docker push
```

There is no `mvn clean package` stage because your Python framework does not create a JAR file.
The Docker image itself is the artifact.

## Approach 1

Folder:

```text
06-jenkins-ci-cd/07-image-builder-approach-1
```

Login style:

```text
docker login -u USER -p PASSWORD
```

This works, but Docker/Jenkins may show a warning because the password is passed in the command line.

## Approach 2

Folder:

```text
06-jenkins-ci-cd/08-image-builder-approach-2
```

Login style:

```text
echo PASSWORD | docker login -u USER --password-stdin
```

This is safer and is the recommended approach.

## Jenkins Credential Needed

Create a Jenkins credential:

```text
Kind: Username with password
ID: dockerhub-creds
Username: your Docker Hub username
Password: your Docker Hub password/token
```

The Jenkinsfiles expect this credential ID:

```groovy
DOCKER_HUB = credentials('dockerhub-creds')
```

## Image Name

Current image name in both Jenkinsfiles:

```text
pratyushjindal123/python-selenium
```

If your Docker Hub username/repository is different, update:

```groovy
IMAGE_NAME = 'your-dockerhub-user/python-selenium'
```

## Why bat Is Used

Your `Node1` is your Windows machine.
So Jenkins must run Windows commands:

```groovy
bat 'docker build ...'
```

Do not use `sh` on Node1 unless you intentionally run on a Linux node.

## Recommended Folder To Use

Use approach 2 first:

```text
06-jenkins-ci-cd/08-image-builder-approach-2/Jenkinsfile
```

It matches the instructor concept and uses the safer Docker login method.
