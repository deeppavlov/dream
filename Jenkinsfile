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

def notify(status, duration = 0, e = "") {
  if (status == 'start') {
    stages["${env.STAGE_NAME}"] = 'running ▶'
  }
  else if (status == 'failed') {
    stages["${env.STAGE_NAME}"] = "failed ❌ ${currentBuild.durationString.replace(' and counting', '')} with ${e}"
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

  agent {
    label 'gpu9'
  }

  environment {
    AGENT_PORT=4242
    WAIT_TIMEOUT=900
    WAIT_INTERVAL=10
    COMPOSE_DOCKER_CLI_BUILD=1
    DOCKER_BUILDKIT=1
    COMPOSE_HTTP_TIMEOUT=120
  }

  stages {

    stage('Checkout') {

      steps {
        script {
          def branch = "Current branch is ${env.BRANCH_NAME}"
          if (isPullRequest) {
            echo """${branch}
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
        changeRequest target: '*', comparator: 'GLOB'
        beforeAgent true
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
              notify('failed', e.getMessage(), duration)
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
        changeRequest target: '*', comparator: 'GLOB'
        beforeAgent true
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
              notify('failed', e.getMessage(), duration)
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

    stage('Tests') {

      when {
        changeRequest target: '*', comparator: 'GLOB'
        beforeAgent true
      }

      parallel {

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
        cleanup {
          script {
            notify('cleanup')
            sh './tests/runtests.sh MODE=clean'
          }
        }
      }
    }
  }

  post {
    aborted {
      script {
        notify('aborted')
      }
    }
  }
}
