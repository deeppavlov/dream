node {
    try {
        stage('Clean') {
            sh "rm -rf .[^.] .??* *"
        }
        stage('Checkout') {
            checkout scm
        }
        stage('Tests') {
           sh "./tests/runtests.sh"
        }
    } finally {
        archiveArtifacts artifacts: 'tests/dream/*.csv', fingerprint: true
    }
}