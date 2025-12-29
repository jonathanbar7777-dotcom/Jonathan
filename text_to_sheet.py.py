from music21 import stream, note, converter, environment
from music21 import environment
environment.set('musicxmlPath', r'C:\\Users\\jonat\\Downloads\\MuseStudio\\bin\\MuseScore4.exe')


# מיפוי בסיסי של אותיות לתווים
mapping = {
    'A': 'C4', 'B': 'D4', 'C': 'E4', 'D': 'F4', 'E': 'G4',
    'F': 'A4', 'G': 'B4', 'H': 'C5', 'I': 'D5', 'J': 'E5',
    'K': 'F5', 'L': 'G5', 'M': 'A5', 'N': 'B5', 'O': 'C6',
    'P': 'D6', 'Q': 'E6', 'R': 'F6', 'S': 'G6', 'T': 'A6',
    'U': 'B6', 'V': 'C7', 'W': 'D7', 'X': 'E7', 'Y': 'F7', 'Z': 'G7',
    ' ': 'R'
}

def text_to_score(text, output="output.musicxml"):
    s = stream.Score()
    p = stream.Part()

    for char in text.upper():
        symbol = mapping.get(char, 'R')
        if symbol == 'R':
            p.append(note.Rest(quarterLength=1))
        else:
            n = note.Note(symbol)
            n.quarterLength = 1
            p.append(n)

    s.append(p)
    s.write('musicxml', fp=output)
    print(f"🎼 Notes File Created: {output}")

    # פתיחה אוטומטית ב-MuseScore
    try:
        s.show()  # יפעיל את MuseScore ויציג את התווים
    except:
        print("Failed Opening, Open manually", output)

# דוגמה להפעלה:
if __name__ == "__main__":
    text = input("Enter Text: ")
    text_to_score(text)
