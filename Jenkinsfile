pipeline {
  agent none

  environment {
    WAIT_TIMEOUT=2400
    WAIT_INTERVAL=10
    COMPOSE_HTTP_TIMEOUT=120
  }
  stages {
    stage('Tests') {
      agent {
        label 'dream'
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
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh 'tests/runtests.sh MODE=build'
                }
                catch (Exception e) {
                  int duration = (currentBuild.duration - startTime) / 1000
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
              }
            }
          }
        }

        stage('Start') {
          steps {
            script {
              startTime = currentBuild.duration
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
              }
            }
            aborted {
              script {
                sh 'tests/runtests.sh MODE=clean'
              }
            }
          }
        }

        stage('Test skills') {
          steps {
            script {
              startTime = currentBuild.duration
              Exception ex = null
              catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                try {
                  sh label: 'test skills', script: 'tests/runtests.sh MODE=test_skills'
                }
                catch (Exception e) {
                  int duration = (currentBuild.duration - startTime) / 1000
                  throw e
                }
              }
            }
          }
          post {
            success {
              script {
                int duration = (currentBuild.duration - startTime) / 1000
              }
            }
            aborted {
              script {
                sh 'tests/runtests.sh MODE=clean'
              }
            }
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
