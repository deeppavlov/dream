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
        }
        if (env.BRANCH_NAME == 'dev') {
            stage('CollectPredictions') {
               sh "./tests/runtests.sh MODE=infer_questions"
            }
        }
    } finally {
        archiveArtifacts artifacts: 'tests/dream/output/*', fingerprint: true
        sh "./tests/runtests.sh MODE=clean"
    }
}
