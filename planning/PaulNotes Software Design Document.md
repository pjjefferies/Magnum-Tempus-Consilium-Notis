# PaulNotes Software Design Document

1. About
    1. What is the software applicatoin or feature?
        - A system for tracking tasks, projects and reference notes with GTD functionality with Android and Windows capability, synced over the internet.
    2. Who is it intended for?
        - Initially, just me. Potentially for sharing notes with others in latter stages.
    3. What problem does the software solve?
        - Personal organizaton. Existing solutions are either too expensive or lack desired functions.
    4. How is it going to work?
        - Similar for Android and Windows
        - Main page allows showing Notes or Projects or create new of either
        - Notes allow filtering by context (where) and when
        - Notes sorted by Tag/context/when/reminder time for notification and daily email "to do" list
        - Notes can have reminder times
        - Project allows list of sequential or parallel tasks
        - Project allows where/when to be assigned to each tasks
        - When tasks are added to Projects, they become individual, linked Notes
        - Reference notes have no where/when but have subject tags. They can have reminders too.
    5. What are the main concepts that are involved and how are they related?
        - x

2. User Interface
    - Windows and Android Versions
        - Main User Stories
            - Add a task/note - enter text
                - One button to start
                - Note created, start by entering text for title
                - Option to add other text
                - Option to add picture from camera or from saved
                - Option to where and/or when context
                - Option to add refference tags
                - Option to delete
                - Set a reminder date/time
            - Add a task/note by taking a picture
                - One button to start
                - Note created, start by entering text for title
                - Option to add other text
                - Option to add more pictures from camera or from saved
                - Option to where and/or when context
                - Option to add refference tags
                - Option to delete
                - Set a reminder date/time
            - Create a project
                - One button to start
                - Add tasks
                    - In sequence or parallel
                    - Add where/when context
                    - Add reminders
                    - Indication for completed tasks (check, cross-out)
                        - What happens to tasks when they are part of a project but complete - separate status?
            - Filter tasks shown by context (where/when)
            - Sort tasks by
                - When created
                - Reminder date/time
                - Alphabetical
            - View task/note
                - Option to edit
                    - Same other options as when creating
                - Option to delete
3. Technical Specification
    - What technical details need developers to know to develop the software?
        - ?
    - Are there new tables to add to the database? Fields?
        - Consider dual real database with regular text/json/YAML back-up
        - Primary Database
            - Database TBD - NoSQL?
            - Table - Tasks
            - Table - Reference Notes
            - Table - Projects
        - Text Back-up
            - Tasks/Notes/Projects - Dictionaries
    - How will the software technically work? Are there particular algorithms or libraries that are important?
        - ?
    - What will be the overall design? Which classes are needed? What design patterns are used to model the concepts and relationships?
        - Use UML to draw main classes
        - Consider SOLID design principles
    - What third-party software is neede to build the software or feature?
        - ?
    - Edge cases?
        - ?
    - What should happen in case of a network connection error?
        - ?
4. Testing and Security
    - Are there specific coverage goals for the unit tests?
        - ?
    - What kinds of tests are needed (unit, regression, end-to-end, etc.)?
        - ?
    - What security checks need to be in-place to allow the software to ship?
        - ?
    - How does the feature impact the security of the software? Is there a need for a security audit before the feature is shipped?
        - ?
5. Deployment
    - Are there any architectural or DevOps changes needed?
        - ?
    - Are there any migration scripts that need to be written?
        - From Evernote. Empty Trash before exporting from Evernote
    - Enviroments
        - Develop
        - Test
        - Acceptance (staging)
        - Production
6. Planning
    - Development Timing / Cost
    - Steps - timing by step
    - Development milestones
    - Main risk factors. Alternative routes if infeasibilities found.
    - What parts are absolutely required. What parts can optionally done at a later time?
7. Broader Context
    - What are limitations of the current design?
    - What are possible extensions to think about for the future?
    - Any other considerations?