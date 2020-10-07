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

slackResponse = slackSend(message: generateMsg(stages))
started = false

def notify(status, e = "") {
  if (status == 'start') {
    stages["${env.STAGE_NAME}"] = 'running ▶'
  }
  else if (status == 'failed') {
    stages["${env.STAGE_NAME}"] = "failed ❌ ${duration}s with ${e}"
  }
  else if (status == 'success') {
    stages["${env.STAGE_NAME}"] = "success ✅ ${currentBuild.durationString.replace(' and counting', '')}"
  }
  else if (status == 'aborted') {
    stages["$env.STAGE_NAME}"] = "aborted ⏹"
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

  when {
    changeRequest target: '*', comparator: 'GLOB'
    beforeAgent true
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
          notify('start')
          sh 'tests/runtests.sh MODE=build'
        }
      }

      post {
        failure {
          script {
            notify('failed')
            sh 'tests/runtests.sh MODE=clean'
          }
        }
        success {
          script {
            notify('success')
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
          notify('start')
          sh 'tests/runtests.sh MODE=start'
        }
      }

      post {
        failure {
          script {
            notify('failed')
            sh 'tests/runtests.sh MODE=clean'
          }
        }
        success {
          started = true
          script {
            notify('success')
          }
        }
      }
    }

    stage('Tests') {

      when {
        changeRequest target: '*', comparator: 'GLOB'
        beforeAgent true
      }

      stages {

        stage('Test dialog') {
          steps {
            script {
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh 'tests/runtests.sh MODE=test_dialog'
                }
                catch (Exception e) {
                  notify('failed', e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                notify('success')
              }
            }
          }
        }

        stage('Test skills') {

          steps {
            script {
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh 'tests/runtests.sh MODE=test_skills'
                }
                catch (Exception e) {
                  notify('failed', e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                notify('success')
              }
            }
          }
        }

        /*stage('Collect Predictions') {

          steps {
            script {
              notify('start')
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh './tests/runtests.sh MODE=infer_questions'
                }
                catch (Exception e) {
                  notify('failed', e.getMessage())
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                notify('success')
              }
            }
          }
        }*/
      }

      /*post {
        failure {
          script {
            sh 'tests/runtests.sh MODE=clean'
          }
        }
        success {
          script {
            sh 'tests/runtests.sh MODE=clean'
          }
        }
      }*/
    }

    /*stage('Cleanup') {

      steps {
        script {
          sh './tests/runtests.sh MODE=clean'
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
//    failure {
//      script {
//        if (isPullRequest) {
//          pullRequest.setLabels(['Failure'])
//        }
//      }
//    }
    cleanup {
      script {
        if (started) {
          sh './tests/runtests.sh MODE=clean'
        }
      }
    }
  }
}
