#!/usr/bin/env/groovy

node() {
    stage('checkout') {
        checkout scm
    }
    stage('unit tests') {
        sh 'python setup.py test'
    }
    stage('build distribution') {
        sh 'python setup.py sdist'
    }
    stage('Archive Artifacts') {
        archiveArtifacts artifacts: "dist/*.gz", fingerprint: true
    }
}
