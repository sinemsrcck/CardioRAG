from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.core import answer

if __name__ == '__main__':
    print('CardioRAG hazir. Cikmak icin q yazin.')
    while True:
        question = input('\nSorunuz: ').strip()
        if question.lower() in ('q', 'quit', 'exit'):
            break
        if not question:
            continue
        try:
            response, sources = answer(question)
            print('\nYANIT:\n' + response)
            if sources:
                print('\nGETIRILEN KAYNAKLAR:')
                for s in sources:
                    print(f'[{s["number"]}] {s["filename"]} - sayfa {s["page"]}')
        except Exception as exc:
            print(f'HATA: {exc}')
