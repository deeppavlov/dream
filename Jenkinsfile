#!groovy

def isPullRequest = env.CHANGE_ID ? true : false
//def BuildBadge = addEmbeddableBadgeConfiguration(id: "build", subject: "Build")
stages = [:]

def generateMsg(stages) {
  msg = "${env.BUILD_TAG}"
  for (stage in stages) {
    msg += "\n${stage.key}: ${stage.value}"
  }
  return msg
}

startTime = currentBuild.duration
slackResponse = slackSend(message: generateMsg(stages))
started = false

def notify(status, duration = 0, e = "") {
  if (status == 'start') {
    stages["${env.STAGE_NAME}"] = 'running ▶'
  }
  else if (status == 'failed') {
    stages["${env.STAGE_NAME}"] = "failed ❌ ${duration}s with ${e}"
  }
  else if (status == 'success') {
    stages["${env.STAGE_NAME}"] = "success ✅ ${duration}s"
  }
  else if (status == 'aborted') {
    stages["${env.STAGE_NAME}"] = "aborted ⏹"
  }
  else if (status == 'cleanup') {
    stages["${env.STAGE_NAME}"] = "cleanup ♻"
  }
  slackSend(channel: slackResponse.channelId, message: generateMsg(stages), timestamp: slackResponse.ts)
}


pipeline {

  agent none

  environment {
    AGENT_PORT=4242
    WAIT_TIMEOUT=2400
    WAIT_INTERVAL=10
    COMPOSE_DOCKER_CLI_BUILD=1
    DOCKER_BUILDKIT=1
    COMPOSE_HTTP_TIMEOUT=120
    AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
    AWS_SECRET_ACCESS_KEY='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'
    AWS_DEFAULT_REGION='us-east-1'
  }

  stages {

    stage('Build-prod') {
      agent {
        kubernetes {
          label 'slave'
          yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: slave
spec:
  nodeSelector:
    jenkins: slave
  containers:
  - name: jenkins-agent
    image: 263182626354.dkr.ecr.us-east-1.amazonaws.com/jenkins-agent
    imagePullPolicy: Always
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
    - name: dockersock
      mountPath: "/var/run/docker.sock"
  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
      type: File
"""
        }
      }

      when {
        buildingTag()
        beforeAgent true
      }

      environment {
        VERSION="${TAG_NAME}"
        ENV_FILE='.env.b'
        DP_AGENT_PORT=4242
        DOCKER_REGISTRY='263182626354.dkr.ecr.us-east-1.amazonaws.com'
        DOCKER_BUILDKIT=1
        COMPOSE_DOCKER_CLI_BUILD=1
      }

      steps {
        container('jenkins-agent') {
          script {
            int startTime = currentBuild.duration
            notify('start')
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              try {
                sh label: 'login to ecr', script: 'aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $DOCKER_REGISTRY'
                sh label: 'ecr create repo', script: '''for service in $(docker-compose -f docker-compose.yml -f dev.yml ps --services | grep -wv -e mongo)
                    do
                      aws ecr describe-repositories --repository-names $service || aws ecr create-repository --repository-name $service
                    done
                    '''
                sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                sh label: 'docker build', script: 'docker-compose -f docker-compose.yml -f dev.yml -f staging.yml -f network.yml build'
                sh label: 'docker push', script: 'docker-compose -f docker-compose.yml -f dev.yml -f staging.yml push'
              }
              catch (Exception e) {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('failed', duration, e.getMessage())
                throw e
              }
            }
          }
        }
      }

      post {
        failure {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('failed', duration)
          }
        }
        success {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
      }
    }

    stage('Deploy-prod') {
      agent {
        kubernetes {
          label 'slave'
          yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: slave
spec:
  containers:
  - name: jenkins-agent
    image: 263182626354.dkr.ecr.us-east-1.amazonaws.com/jenkins-agent
    imagePullPolicy: Always
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
    - name: dockersock
      mountPath: "/var/run/docker.sock"
  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
      type: File
"""
        }
      }

      when {
        buildingTag()
        beforeAgent true
      }

      environment {
        VERSION="${TAG_NAME}"
        ENV_FILE='.env.b'
        ENV_CM='env-b'
        DOCKER_REGISTRY='263182626354.dkr.ecr.us-east-1.amazonaws.com'
        NAMESPACE='alexa-b'
        ENVIRONMENT='B'
      }

      steps {
        container('jenkins-agent') {
          script {
            int startTime = currentBuild.duration
            notify('start')
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              try {
                sh label: 'update kubeconfig', script: 'aws eks update-kubeconfig --name alexa'
                sh label: 'update environment', script: "kubectl delete configmap ${ENV_CM} -n ${NAMESPACE} && kubectl create configmap ${ENV_CM} -n ${NAMESPACE} --from-env-file ${ENV_FILE}"
                sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                sh label: 'deploy', script: 'for dir in kubernetes/models/*; do kubectl apply -f $dir || true; done'
              }
              catch (Exception e) {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('failed', duration, e.getMessage())
                throw e
              }
            }
          }
        }
      }

      post {
        failure {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('failed', duration)
          }
        }
        success {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
      }
    }

    stage('Build-dev') {
      agent {
        kubernetes {
          label 'slave'
          yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: slave
spec:
  nodeSelector:
    jenkins: slave
  containers:
  - name: jenkins-agent
    image: 263182626354.dkr.ecr.us-east-1.amazonaws.com/jenkins-agent
    imagePullPolicy: Always
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
    - name: dockersock
      mountPath: "/var/run/docker.sock"
  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
      type: File
"""
        }
      }

      when {
        branch pattern: 'dev', comparator: 'EQUALS'
        beforeAgent true
      }

      environment {
        VERSION='latest'
        ENV_FILE='.env.dev'
        DP_AGENT_PORT=4242
        DOCKER_REGISTRY='263182626354.dkr.ecr.us-east-1.amazonaws.com'
        DOCKER_BUILDKIT=1
        COMPOSE_DOCKER_CLI_BUILD=1
      }

      steps {
        container('jenkins-agent') {
          script {
            int startTime = currentBuild.duration
            notify('start')
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              try {
                sh label: 'login to ecr', script: 'aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $DOCKER_REGISTRY'
                sh label: 'ecr create repo', script: '''for service in $(docker-compose -f docker-compose.yml -f dev.yml ps --services | grep -wv -e mongo)
                    do
                      aws ecr describe-repositories --repository-names $service || aws ecr create-repository --repository-name $service
                    done
                    '''
                sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                sh label: 'docker build', script: 'docker-compose -f docker-compose.yml -f dev.yml -f staging.yml -f network.yml build'
                sh label: 'docker push', script: 'docker-compose -f docker-compose.yml -f dev.yml -f staging.yml push'
              }
              catch (Exception e) {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('failed', duration, e.getMessage())
                throw e
              }
            }
          }
        }
      }

      post {
        failure {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('failed', duration)
          }
        }
        success {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
      }
    }

    stage('Deploy-dev') {
      agent {
        kubernetes {
          label 'slave'
          yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    jenkins: slave
spec:
  containers:
  - name: jenkins-agent
    image: 263182626354.dkr.ecr.us-east-1.amazonaws.com/jenkins-agent
    imagePullPolicy: Always
    command:
    - cat
    tty: true
    securityContext:
      privileged: true
    volumeMounts:
    - name: dockersock
      mountPath: "/var/run/docker.sock"
  volumes:
  - name: dockersock
    hostPath:
      path: /var/run/docker.sock
      type: File
"""
        }
      }

      when {
        branch pattern: 'dev', comparator: 'EQUALS'
        beforeAgent true
      }

      environment {
        VERSION='latest'
        ENV_FILE='.env.dev'
        ENV_CM='env-dev'
        DOCKER_REGISTRY='263182626354.dkr.ecr.us-east-1.amazonaws.com'
        NAMESPACE='alexa'
        ENVIRONMENT='dev'
      }

      steps {
        container('jenkins-agent') {
          script {
            int startTime = currentBuild.duration
            notify('start')
            catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
              try {
                sh label: 'update kubeconfig', script: 'aws eks update-kubeconfig --name alexa'
                sh label: 'update environment', script: 'kubectl delete configmap ${ENV_CM} -n ${NAMESPACE} && kubectl create configmap ${ENV_CM} -n ${NAMESPACE} --from-env-file $ENV_FILE'
                sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                sh label: 'deploy', script: 'for dir in kubernetes/models/*; do kubectl apply -f $dir || true; done'
              }
              catch (Exception e) {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('failed', duration, e.getMessage())
                throw e
              }
            }
          }
        }
      }

      post {
        failure {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('failed', duration)
          }
        }
        success {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
      }
    }


    stage('Checkout') {

      agent {
        label 'gpu9'
      }

      when {
        changeRequest target: 'dev', comparator: 'GLOB'
        beforeAgent true
      }

      steps {
        script {
          def branch = "Current branch is ${env.BRANCH_NAME}"
          if (isPullRequest) {
            echo """${branch}
            Git commiter name: ${env.GIT_AUTHOR_NAME} or ${env.GIT_COMMITTER_NAME}
            Pull request: merge ${env.CHANGE_BRANCH} into ${env.CHANGE_TARGET}
            Pull request id: ${pullRequest.id} or ${env.CHANGE_ID}
            Pull request title: ${pullRequest.title}
            Pull request headRef: ${pullRequest.headRef}
            Pull request base: ${pullRequest.base}
            """
          }
          else {
            echo "${branch}"
          }
        }
      }
    }

    stage('Build') {

      when {
        changeRequest target: 'dev', comparator: 'GLOB'
        beforeAgent true
      }

      agent {
        label 'gpu9'
      }

      steps {
        script{
          startTime = currentBuild.duration
          notify('start')
          Exception ex = null
          catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
            try {
              sh 'tests/runtests.sh MODE=build'
            }
            catch (Exception e) {
              int duration = (currentBuild.duration - startTime) / 1000
              notify('failed', duration, e.getMessage())
              throw e
            }
          }
        }
      }

      post {
        failure {
          script {
            sh 'tests/runtests.sh MODE=clean'
          }
        }
        success {
          script {
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
      }

    }

    stage('Start') {

      when {
        changeRequest target: 'dev', comparator: 'GLOB'
        beforeAgent true
      }

      agent {
        label 'gpu9'
      }

      steps {
        script {
          startTime = currentBuild.duration
          notify('start')
          Exception ex = null
          catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
            try {
              sh 'tests/runtests.sh MODE=start'
            }
            catch (Exception e) {
              int duration = (currentBuild.duration - startTime) / 1000
              notify('failed', duration, e.getMessage())
              throw e
            }
          }
        }
      }

      post {
        failure {
          script {
            sh 'tests/runtests.sh MODE=clean'
          }
        }
        success {
          script {
            started = true
            int duration = (currentBuild.duration - startTime) / 1000
            notify('success', duration)
          }
        }
        aborted {
          script {
            notify('aborted')
          }
        }
      }
    }

    stage('Tests') {

      when {
        changeRequest target: 'dev', comparator: 'GLOB'
        beforeAgent true
      }

      agent {
        label 'gpu9'
      }

      stages {

        stage('Test dialog') {
          steps {
            script {
              startTime = currentBuild.duration
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh 'tests/runtests.sh MODE=test_dialog'
                }
                catch (Exception e) {
                  int duration = (currentBuild.duration - startTime) / 1000
                  notify('failed', duration, e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('success', duration)
              }
            }
            aborted {
              script {
                notify('aborted')
              }
            }
          }
        }

        stage('Test skills') {

          steps {
            script {
              startTime = currentBuild.duration
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh 'tests/runtests.sh MODE=test_skills'
                }
                catch (Exception e) {
                  int duration = (currentBuild.duration - startTime) / 1000
                  notify('failed', duration, e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('success', duration)
              }
            }
            aborted {
              script {
                notify('aborted')
              }
            }
          }
        }

        /*stage('Collect Predictions') {

          steps {
            script {
              startTime = currentBuild.duration
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh './tests/runtests.sh MODE=infer_questions'
                }
                catch (Exception e) {
                  int duration = (currentBuild.duration - startTime) / 1000
                  notify('failed', duration, e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                int duration = (currentBuild.duration - startTime) / 1000
                notify('success', duration)
              }
            }
          }
        }*/
      }
      post {
        aborted {
          script {
            notify('aborted')
          }
        }
        cleanup {
          script {
            if (started) {
              notify('cleanup')
              sh './tests/runtests.sh MODE=clean'
            }
          }
        }
      }
    }
  }
}
