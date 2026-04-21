# Animals Letter Graph

`animals.py` reads animal names from a text file or stdin, normalizes capitalization, and builds an interactive directed graph where each name connects its first letter to its last letter.

The default output is an HTML graph opened in your browser. Nodes start in a fixed readable layout, stay still unless you drag them, and the canvas supports pan and zoom. Edge labels show how many animal names map to each letter pair, and hovering an edge shows the contributing names.

Examples:

```bash
python animals.py animals.txt
python animals.py animals.txt --controls
python animals.py animals.txt --output animals_graph.html
python animals.py animals.txt --no-show --output animals_graph.html
cat animals.txt | python animals.py
```
