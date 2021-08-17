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
    WAIT_TIMEOUT=2400
    WAIT_INTERVAL=10
    COMPOSE_HTTP_TIMEOUT=120
    //AWS_ACCESS_KEY_ID='AKIAT2RXIFYZLDB66LZ3'
    //AWS_SECRET_ACCESS_KEY='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'
    //AWS_DEFAULT_REGION='us-east-1'
    AWS_ACCESS_KEY_ID='AKIA5U27I4UTIJ7QJJ5L'
    AWS_SECRET_ACCESS_KEY='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'
    AWS_DEFAULT_REGION='us-west-2'
  }

  stages {

    stage('Dev') {

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
        ENV_FILE='.env.staging'
        DP_AGENT_PORT=4242
        //DOCKER_REGISTRY='263182626354.dkr.ecr.us-east-1.amazonaws.com'
        DOCKER_REGISTRY='938113295654.dkr.ecr.us-west-2.amazonaws.com'
        NAMESPACE='alexa'
        ENVIRONMENT='dev'
        //CHECK_URL="http://ab61c7a0598e44dcbab6b2c216e108de-1052105272.us-east-1.elb.amazonaws.com:4242/ping"
        CHECK_URL="http://agent.alexa.svc:4242/ping"
      }

      stages {

        stage ('Build-dev') {

          steps {
            container('jenkins-agent') {
              script {
                int startTime = currentBuild.duration
                notify('start')
                try {
                  sh label: 'login to ecr', script: 'aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $DOCKER_REGISTRY'
                  sh label: 'ecr create repo', script: '''for service in $(docker-compose -f docker-compose.yml ps --services | grep -wv -e mongo)
                      do
                        aws ecr describe-repositories --repository-names $service || aws ecr create-repository --repository-name $service
                      done
                      '''
                  sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                  sh label: 'docker build', script: 'docker-compose -f docker-compose.yml -f staging.yml -f network.yml build'
                  sh label: 'docker push', script: 'docker-compose -f docker-compose.yml -f staging.yml push'
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

          steps {
            container('jenkins-agent') {
              script {
                int startTime = currentBuild.duration
                notify('start')
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                  try {
                    sh label: 'update kubeconfig', script: 'aws eks update-kubeconfig --name staging'
                    sh label: 'update environment', script: 'kubectl create configmap env -n ${NAMESPACE} --from-env-file $ENV_FILE -o yaml --dry-run=client | kubectl apply -f -'
                    sh label: 'generate deployment', script: 'python3 kubernetes/kuber_generator.py'
                    sh label: 'remove redundant pods', script: '''
                      for dp in $(kubectl -n ${NAMESPACE} get deploy  --no-headers -o custom-columns=":metadata.name" | grep -e '-dp$');
                      do
                        kubectl delete deploy $dp -n ${NAMESPACE}
                      done
                    '''
                    sh label: 'deploy', script: 'for dir in kubernetes/models/*; do kubectl apply -f $dir || true; done'
                    sh label: 'recreate pods', script: 'for dp in kubernetes/models/*/*-dp.yaml; do kubectl rollout restart -n ${NAMESPACE} deploy $(basename ${dp%.*}); done'
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

        stage('Is-running-dev') {

          steps {
            container('jenkins-agent') {
              script {
                int startTime = currentBuild.duration
                notify('start')
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                  try {
                    sh label: 'is agent running', script: 'tests/wait_service.sh'
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
      } // end of stages
    } // end of dev

    stage('Tests') {

      agent {
        label 'dream'
      }

      when {
        changeRequest target: 'dev', comparator: 'GLOB'
        not {
          changeRequest title: '(?i)\bwip\b.*', comparator: 'REGEXP'
        }
        not {
          changeRequest title: '(?i).*\bskip-ci\b.*', comparator: 'REGEXP'
        }
        beforeAgent true
      }

      stages {

        stage('Checkout') {

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

          steps {
            script {
              startTime = currentBuild.duration
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh '''
                        cat test.yml
                  '''
                  sh 'tests/runtests.sh MODE=clean && tests/runtests.sh MODE=start'
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
                sh 'tests/runtests.sh MODE=clean'
              }
            }
          }
        }

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
            always {
              script {
                archiveArtifacts artifacts: 'tests/dream/output/*', fingerprint: true
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
                  sh label: 'test skills', script: 'tests/runtests.sh MODE=test_skills'
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
./tests/runtests.sh MODE=clean
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
      } // end of stages
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
    } // end of Tests
  } // end of stages
}
