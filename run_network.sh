#!/bin/bash


cd "$(dirname "$0")"

source venv/bin/activate

streamlit run app.py > streamlit.log 2>&1 &
STREAMLIT_PID=$!

echo "Streamlit lancé (PID=$STREAMLIT_PID)."
echo "Ouvre ton navigateur sur : http://localhost:8501"
echo "You can now type commands below, for example: add-node r1"
echo ""

python cli.py repl


echo "Arrêt de Streamlit..."
kill "$STREAMLIT_PID"
