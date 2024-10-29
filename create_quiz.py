import json
import uuid
from datetime import datetime


def read_markdown_questions(filename):
    """Read and parse markdown questions from a file."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = []
    current_question = None
    current_choices = []

    for line in content.split('\n'):
        line = line.strip()
        if not line:  # Empty line indicates end of current question
            if current_question:
                questions.append({
                    'question': current_question,
                    'choices': current_choices
                })
                current_question = None
                current_choices = []
        elif line.startswith('- ') or line.startswith('* '):
            choice = line[2:].strip()
            current_choices.append(choice)
        elif not line.startswith('- ') and not current_question:
            current_question = line

    if current_question:
        questions.append({
            'question': current_question,
            'choices': current_choices
        })

    return questions


def create_question_element(survey_id, question_text, choices, qid_num):
    """Create a Qualtrics SQ element."""
    qid = f"QID{qid_num}"
    return {
        "SurveyID": survey_id,
        "Element": "SQ",
        "PrimaryAttribute": qid,
        "SecondaryAttribute": question_text,
        "TertiaryAttribute": None,
        "Payload": {
            "QuestionText": question_text,
            "DefaultChoices": False,
            "DataExportTag": f"Q{qid_num}",
            "QuestionType": "MC",
            "Selector": "SAVR",
            "SubSelector": "TX",
            "Configuration": {
                "QuestionDescriptionOption": "UseText"
            },
            "QuestionDescription": question_text,
            "Choices": {
                str(i+1): {"Display": choice}
                for i, choice in enumerate(choices)
            },
            "ChoiceOrder": [str(i+1) for i in range(len(choices))],
            "Validation": {
                "Settings": {
                    "ForceResponse": "ON",
                    "ForceResponseType": "ON",
                    "Type": "None"
                }
            },
            "Language": [],
            "NextChoiceId": len(choices) + 1,
            "NextAnswerId": 1,
            "QuestionID": qid,
            "DataVisibility": {
                "Private": False,
                "Hidden": False
            },
            "Randomization": {
                "Advanced": None,
                "Type": "All",
                "TotalRandSubset": ""
            }
        }
    }


def update_qsf_template(template_data, markdown_questions, password=None, title=None):
    """Update QSF template with new questions from markdown."""
    survey_id = template_data["SurveyEntry"]["SurveyID"]

    # Update title if provided
    if title:
        template_data["SurveyEntry"]["SurveyName"] = title

    # Update password if provided
    if password or title:
        for element in template_data["SurveyElements"]:
            if element["Element"] == "SO":
                if password:
                    element["Payload"]["Password"] = password
                if title:
                    element["Payload"]["SurveyTitle"] = title

    # Update last modified timestamp
    template_data["SurveyEntry"]["LastModified"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S")

    # Keep only identification questions and required elements
    kept_elements = []
    for element in template_data["SurveyElements"]:
        if element["Element"] in ["BL", "FL", "PL", "RS", "SO", "QGO", "SCO", "PROJ", "STAT", "QC"]:
            kept_elements.append(element)
        elif element["Element"] == "SQ" and element["PrimaryAttribute"] in ["QID2", "QID8", "QID9"]:
            kept_elements.append(element)

    # Create new question elements
    start_qid = 10
    question_elements = []
    block_elements = []

    for idx, q in enumerate(markdown_questions):
        qid = f"QID{start_qid + idx}"

        # Create question element
        question_elements.append(create_question_element(
            survey_id,
            q['question'],
            q['choices'],
            start_qid + idx
        ))

        # Create block element
        block_elements.append({
            "Type": "Standard",
            "SubType": "",
            # Start after identification block
            "Description": f"Block {idx + 3}",
            "ID": f"BL_{str(uuid.uuid4()).replace('-', '')}",
            "BlockElements": [{"Type": "Question", "QuestionID": qid}]
        })

    # Update blocks
    for element in kept_elements:
        if element["Element"] == "BL":
            # Keep identification block
            payload = {
                "2": next(block for block in element["Payload"].values()
                          if block.get("Description") == "Identifiers")
            }
            # Add new question blocks
            for i, block in enumerate(block_elements):
                payload[str(i + 3)] = block  # Start after identification block
            element["Payload"] = payload

    # Update survey flow
    for element in kept_elements:
        if element["Element"] == "FL":
            # Start with identification block
            flow_items = [
                {
                    # Keep original ID block
                    "ID": element["Payload"]["Flow"][0]["ID"],
                    "Type": "Standard",
                    "FlowID": "FL_3"
                }
            ]

            # Add new question blocks
            for i, block in enumerate(block_elements):
                flow_items.append({
                    "ID": block["ID"],
                    "Type": "Standard",
                    "FlowID": f"FL_{i + 4}"  # Start after identification
                })

            element["Payload"]["Flow"] = flow_items
            element["Payload"]["Properties"]["Count"] = len(flow_items) * 2

    # Update question count
    for element in kept_elements:
        if element["Element"] == "QC":
            element["SecondaryAttribute"] = str(
                3 + len(markdown_questions))  # 3 ID questions + new questions

    # Combine all elements
    template_data["SurveyElements"] = kept_elements + question_elements

    return template_data


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Update Qualtrics quiz template with new questions.')
    parser.add_argument(
        '--password', help='Set the survey password', default=None)
    parser.add_argument('--title', help='Set the survey title', default=None)
    parser.add_argument('--input', help='Set the input file',
                        default='markdown_questions.md')
    parser.add_argument('--output', help='Set the output quiz name',
                        default='updated_survey.qsf')
    args = parser.parse_args()

    # Read the markdown questions
    try:
        questions = read_markdown_questions(args.input)
    except FileNotFoundError:
        print("Error: %s not found!" % args.input)
        return

    # Read the template
    try:
        with open('template.qsf', 'r', encoding='utf-8') as f:
            template = json.load(f)
    except FileNotFoundError:
        print("Error: template.qsf not found!")
        return

    # Update the template
    updated_template = update_qsf_template(
        template,
        questions,
        password=args.password,
        title=args.title
    )

    # Write the updated template
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(updated_template, f, indent=4)

    print("Successfully created %s!" % args.output)


if __name__ == "__main__":
    main()
