node {
    try {
        stage('Clean') {
            sh "rm -rf .[^.] .??* *"
        }
        stage('Checkout') {
            checkout scm
        }
        stage('Tests') {
           sh "./tests/runtests.sh MODE=test_dialog"
           currentBuild.result = 'SUCCESS'
        }
        if (env.BRANCH_NAME == 'dev') {
            stage('CollectPredictions') {
               sh "./tests/runtests.sh MODE=infer_questions"
            }
        }
    } catch(e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        archiveArtifacts artifacts: 'tests/dream/output/*', fingerprint: true
        sh "./tests/runtests.sh MODE=clean"
        def msg = "Build for ${env.BRANCH_NAME} has status ${currentBuild.result}\n${env.BUILD_URL}"
        if (currentBuild.result == 'FAILURE') {
            slackSend color: 'bad', message: msg
        } else {
            slackSend color: 'good', message: msg
        }
    }
}
