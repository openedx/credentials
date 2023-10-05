/*
 * This is a high level diagram visualizing how a Course credential is awarded to a learner between the monolith and
 * the Credentials IDA. It is written using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        learner = person "Learner" "A learner taking courses on an Open edX site"

        group "edx-platform" {
            grades_app = softwareSystem "Grades Django App"
            certificates_app = softwareSystem "Certificates Django App"
            credentials_lms_app = softwareSystem "Credentials (LMS) Django App"
            programs_app = softwareSystem "Programs Django App"
            celery = softwareSystem "Celery"
            monolith_db = softwareSystem "edx-platform DB"
        }

        group "Credentials IDA" {
            credentials_app = softwareSystem "Credentials Django App"
            api_app = softwareSystem "API Django App"
            credentials_db = softwareSystem "Credentials DB"
            credentials_eb_consumer = softwareSystem "Credentials Event Bus Consumer"
        }

        event_bus = softwareSystem "Event Bus"

        credentials_eb_consumer -> event_bus "Polling, listening for Course Certificate events"

        learner -> grades_app "Earns passing grade in course"
        grades_app -> certificates_app "Emits a `COURSE_GRADE_NOW_PASSED` signal"
        certificates_app -> monolith_db "Award course certificate in LMS"
        certificates_app -> event_bus "Publishes a `CERTIFICATE_CREATED` event"
        certificates_app -> programs_app "Emits a `COURSE_CERT_CHANGED` signal"
        programs_app -> celery "Queues a `award_course_certificate` task"
        celery -> credentials_lms_app "Processes `award_course_certificate` task"
        credentials_lms_app -> api_app "Makes API request to award a course certificate to learner"
        api_app -> credentials_app "Processes API request"
        credentials_eb_consumer -> credentials_app "Processes `CERTIFICATE_CREATED` event"
        credentials_app -> credentials_db "Award (Course) Credential to learner"
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
