#!/usr/bin/env/groovy

node() {
    stage('checkout') {
        checkout scm
    }
    stage('unit tests') {
        sh 'python setup.py test'
    }
}
