/*
 * This is a high level diagram visualizing how a Program credential is awarded to a learner between the monolith and
 * the Credentials IDA. It is written using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        learner = person "Learner" "A learner taking courses on Open edX site"

        group "edx-platform" {
            grades_app = softwareSystem "Grades Django App"
            certificates_app = softwareSystem "Certificates Django App"
            credentials_lms_app = softwareSystem "Credentials (LMS) Django App"
            programs_app = softwareSystem "Programs Django App"
            celery = softwareSystem "Celery"
        }

        group "Credentials IDA" {
            credentials_app = softwareSystem "Credentials Django App"
            api_app = softwareSystem "API Django App"
        }

        event_bus = softwareSystem "Event Bus"

        learner -> grades_app "Earns passing grade in final course of a program"
        grades_app -> certificates_app "Emits a `COURSE_GRADE_NOW_PASSED` signal"
        certificates_app -> programs_app "Emits a `COURSE_CERT_AWARDED` signal"
        programs_app -> celery "Queues an `award_program_certificate` task"
        celery -> credentials_lms_app "Processes `award_program_certificate` task"
        credentials_lms_app -> api_app "Makes API request to award program certificate to learner"
        api_app -> credentials_app "Issues Program Credential to learner"
        credentials_app -> event_bus "Emits `PROGRAM_CERTIFICATE_AWARDED` event to the Event Bus"
    }

    views {
        systemlandscape "SystemLandscape" {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
            }
        }
    }
}
