
# Markdown Quiz to Qualtrics Survey

This is a python script that converts a markdown file into a Qualtrics survey format. The script reads a markdown file, extracts the questions, and adds the questions to a QSF (Qualtrics Survey Format) file. This file can be loaded into Qualtrics to create a survey.

Features (implemented and to implement):
- Read markdown file [Done]
- Implement multiple choice questions [Done]
- Implement open text questions [Todo]
- Implement rating scale questions [Todo]
- Add password to the survey [Done] -- use the --password "newpassword" option on the python script
- Change title of the survey [Done] -- use the --title "newtitle" option on the python script
- Generate answer key for grading [Todo]
- Automatically grade assignments [Todo]

# Example usage:
From the command line:
```
python create_quiz.py --input "markdown_questions.md" --output "survey_quiz.qsf" --title "My Survey" --password "mypassword"
```
