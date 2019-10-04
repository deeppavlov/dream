node {
    stage('Clean') {
        sh "rm -rf .[^.] .??* *"
    }
    stage('Checkout') {
        checkout scm
    }
    stage('Tests') {
       sh "./tests/runtests.sh"
    }
}