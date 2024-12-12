import os
import csv

# Define the path for feedback.csv and x.csv in the current folder
feedback_file = "feedback.csv"
x_file_path = "x.csv"

# Define the start and end columns as Excel-style letters
start_column = " "  # Example: Start column letter
end_column = " "  # Example: End column letter

def column_letter_to_index(letter):
    """Convert Excel column letter to 0-based index."""
    letter = letter.upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1

def process_x_to_feedback(x_file_path, feedback_file, start_column, end_column):
    # Convert column letters to indices
    start_index = column_letter_to_index(start_column)
    end_index = column_letter_to_index(end_column)

    # Check if feedback.csv exists; if not, create it with a header
    if not os.path.exists(feedback_file):
        with open(feedback_file, "w", newline="") as fb_file:
            writer = csv.writer(fb_file)
            writer.writerow(["ID", "Date", "Survey"])

    # Read feedback.csv to determine the next ID
    with open(feedback_file, "r", newline="") as fb_file:
        reader = csv.reader(fb_file)
        next_id = sum(1 for _ in reader)  # Count rows to determine the next ID

    # Process x.csv
    with open(x_file_path, "r", newline="") as x_file:
        x_reader = csv.reader(x_file)
        rows = list(x_reader)

        if len(rows) < 4:
            print("x.csv does not have enough rows to process.")
            return

        header = rows[3]  # Fourth row contains column names (skip first three rows)
        questions = rows[1]  # Second row contains questions
        data_rows = rows[4:]  # Remaining rows contain data

        feedback_rows = []
        for row in data_rows:
            date = row[0]  # First column as the date
            survey_text = "; ".join(
                f"Question: {questions[col]} Answer: {row[col]}" for col in range(start_index, end_index + 1) if col < len(row) and col != 2
            )
            feedback_rows.append([next_id, date, survey_text])
            next_id += 1

    # Append the processed rows to feedback.csv
    with open(feedback_file, "a", newline="") as fb_file:
        writer = csv.writer(fb_file)
        writer.writerows(feedback_rows)

    print(f"Processed {len(feedback_rows)} rows from {x_file_path} into {feedback_file}.")

# Run the processing function
process_x_to_feedback(x_file_path, feedback_file, start_column, end_column)
