from music21 import converter, note

# אותו מיפוי בסיסי כמו בשלב ההצפנה
mapping = {
    'A': 'C4', 'B': 'D4', 'C': 'E4', 'D': 'F4', 'E': 'G4',
    'F': 'A4', 'G': 'B4', 'H': 'C5', 'I': 'D5', 'J': 'E5',
    'K': 'F5', 'L': 'G5', 'M': 'A5', 'N': 'B5', 'O': 'C6',
    'P': 'D6', 'Q': 'E6', 'R': 'F6', 'S': 'G6', 'T': 'A6',
    'U': 'B6', 'V': 'C7', 'W': 'D7', 'X': 'E7', 'Y': 'F7', 'Z': 'G7',
    ' ': 'R'
}

# הפוך את המיפוי כך שנוכל לתרגם תווים בחזרה לאותיות
reverse_mapping = {v: k for k, v in mapping.items()}

def decrypt_score_to_text(filename):
    """
    מקבל קובץ MusicXML (שנוצר על ידי ההצפנה)
    ומחזיר את הטקסט המקורי שהוצפן בתווים
    """
    s = converter.parse(filename)
    result = ""

    for element in s.flat.notesAndRests:
        if isinstance(element, note.Note):
            pitch = element.nameWithOctave
            result += reverse_mapping.get(pitch, '?')  # אם לא מזוהה – '?'
        elif isinstance(element, note.Rest):
            result += ' '

    return result

# דוגמה לשימוש
if __name__ == "__main__":
    file_path = input("Enter File Name: ")
    text = decrypt_score_to_text(file_path)
    print("\n🔍 The Decrypted Text Is\n")
    print(text)
