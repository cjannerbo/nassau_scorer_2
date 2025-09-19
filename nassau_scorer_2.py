import streamlit as st
import pandas as pd

# Page config
st.set_page_config(
    page_title="Nassau Golf Scorer",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better mobile experience
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 20px;
        font-weight: bold;
    }
    .win-button > button {
        background-color: #4CAF50;
        color: white;
    }
    .tie-button > button {
        background-color: #FFC107;
        color: white;
    }
    .loss-button > button {
        background-color: #F44336;
        color: white;
    }
    div[data-testid="column"] {
        padding: 2px;
    }
</style>
""", unsafe_allow_html=True)

def calculate_nine(holes, nine_name):
    """Calculate points for a nine with the new scoring framework"""
    if not any(h is not None for h in holes):
        return {'points': 0, 'details': [], 'presses': []}
    
    bets = []
    details = []
    hole_offset = 0 if 'Front' in nine_name else 9
    
    # Start with original bet
    bets.append({'start': 0, 'name': 'Original', 'triggered': False})
    
    # Find press triggers
    bet_idx = 0
    while bet_idx < len(bets):
        bet = bets[bet_idx]
        running_score = 0
        
        for hole_idx in range(bet['start'], 9):
            if holes[hole_idx] is None:
                break
            
            if holes[hole_idx] == 'W':
                running_score += 1
            elif holes[hole_idx] == 'L':
                running_score -= 1
            
            # Check for press trigger
            if not bet['triggered'] and abs(running_score) >= 2 and hole_idx <= 6:
                bet['triggered'] = True
                press_start = hole_idx + 1
                
                if not any(b['start'] == press_start for b in bets):
                    press_num = len([b for b in bets if 'Press' in b['name']]) + 1
                    bets.append({
                        'start': press_start,
                        'name': f"Press #{press_num}",
                        'triggered': False
                    })
        
        bet_idx += 1
    
    # Calculate total holes won/lost across all 9 holes
    total_holes = 0
    for i in range(9):
        if holes[i] == 'W':
            total_holes += 1
        elif holes[i] == 'L':
            total_holes -= 1
    
    # Calculate bet results (win = +1, loss = -1, tie = 0)
    bet_points = 0
    for bet in bets:
        bet_score = 0
        hole_results = []
        
        for i in range(bet['start'], 9):
            if holes[i] is None:
                break
            if holes[i] == 'W':
                bet_score += 1
                hole_results.append('+')
            elif holes[i] == 'L':
                bet_score -= 1
                hole_results.append('-')
            else:
                hole_results.append('0')
        
        # Determine if bet was won, lost, or tied
        if bet_score > 0:
            bet_result = 'Won'
            bet_point = 1
        elif bet_score < 0:
            bet_result = 'Lost'
            bet_point = -1
        else:
            bet_result = 'Tied'
            bet_point = 0
        
        bet_points += bet_point
        
        start_hole = bet['start'] + 1 + hole_offset
        end_hole = 9 + hole_offset if 'Front' in nine_name else 18
        details.append({
            'bet': bet['name'],
            'holes': f"{start_hole}-{end_hole}",
            'results': ''.join(hole_results),
            'score': bet_score,
            'outcome': bet_result,
            'points': bet_point
        })
    
    # Check for auto-press on hole 9/18
    auto_press_points = 0
    if holes[8] is not None:
        last_bet = bets[-1]
        if last_bet['start'] != 8:
            last_bet_score_thru_8 = 0
            for i in range(last_bet['start'], min(8, 9)):
                if holes[i] is None:
                    break
                if holes[i] == 'W':
                    last_bet_score_thru_8 += 1
                elif holes[i] == 'L':
                    last_bet_score_thru_8 -= 1
            
            # Auto-press if exactly 1 up or 1 down
            if abs(last_bet_score_thru_8) == 1:
                auto_hole = 9 if 'Front' in nine_name else 18
                if holes[8] == 'W':
                    auto_press_points = 1
                    auto_outcome = 'Won'
                elif holes[8] == 'L':
                    auto_press_points = -1
                    auto_outcome = 'Lost'
                else:
                    auto_press_points = 0
                    auto_outcome = 'Tied'
                
                bet_points += auto_press_points
                details.append({
                    'bet': f'Auto-press',
                    'holes': f"{auto_hole}",
                    'results': '+' if holes[8] == 'W' else ('-' if holes[8] == 'L' else '0'),
                    'score': auto_press_points,
                    'outcome': auto_outcome,
                    'points': auto_press_points
                })
    
    total_points = total_holes + bet_points
    
    return {
        'points': total_points, 
        'details': details, 
        'presses': bets[1:],
        'holes_won': total_holes,
        'bet_points': bet_points
    }

def calculate_overall(front_9, back_9):
    """Calculate overall 18 points"""
    total_wins = sum(1 for h in front_9 + back_9 if h == 'W')
    total_losses = sum(1 for h in front_9 + back_9 if h == 'L')
    
    if total_wins > total_losses:
        return 1
    elif total_losses > total_wins:
        return -1
    else:
        return 0

# Initialize session state
if 'front_9' not in st.session_state:
    st.session_state.front_9 = [None] * 9
if 'back_9' not in st.session_state:
    st.session_state.back_9 = [None] * 9
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1

# Title and bet amount
st.title("⛳ Nassau Golf Scorer")
col1, col2 = st.columns([2, 1])
with col1:
    bet_amount = st.number_input("Bet Amount ($)", min_value=1, value=5, step=1)
with col2:
    if st.button("🔄 Reset Game", type="secondary"):
        st.session_state.front_9 = [None] * 9
        st.session_state.back_9 = [None] * 9
        st.session_state.current_hole = 1
        st.rerun()

# Hole navigation
st.markdown("---")
hole_col1, hole_col2, hole_col3 = st.columns([1, 2, 1])
with hole_col1:
    if st.button("← Previous") and st.session_state.current_hole > 1:
        st.session_state.current_hole -= 1
        st.rerun()
with hole_col2:
    st.markdown(f"<h2 style='text-align: center;'>Hole {st.session_state.current_hole}</h2>", unsafe_allow_html=True)
    nine = "Front 9" if st.session_state.current_hole <= 9 else "Back 9"
    st.markdown(f"<p style='text-align: center;'>{nine}</p>", unsafe_allow_html=True)
with hole_col3:
    if st.button("Next →") and st.session_state.current_hole < 18:
        st.session_state.current_hole += 1
        st.rerun()

# Score buttons for current hole
st.markdown("### Record Result:")
col1, col2, col3 = st.columns(3)

hole_idx = (st.session_state.current_hole - 1) % 9
nine = 'front_9' if st.session_state.current_hole <= 9 else 'back_9'

with col1:
    if st.button("+ Win", key=f"win_{st.session_state.current_hole}", use_container_width=True):
        getattr(st.session_state, nine)[hole_idx] = 'W'
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
        st.rerun()

with col2:
    if st.button("0 Tie", key=f"tie_{st.session_state.current_hole}", use_container_width=True):
        getattr(st.session_state, nine)[hole_idx] = 'T'
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
        st.rerun()

with col3:
    if st.button("- Loss", key=f"loss_{st.session_state.current_hole}", use_container_width=True):
        getattr(st.session_state, nine)[hole_idx] = 'L'
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
        st.rerun()

# Display all holes status
st.markdown("---")
st.markdown("### Scorecard")

# Front 9 display
front_cols = st.columns(9)
for i, col in enumerate(front_cols):
    with col:
        result = st.session_state.front_9[i]
        if result == 'W':
            st.markdown(f"**{i+1}**\n\n🟢 +", unsafe_allow_html=True)
        elif result == 'L':
            st.markdown(f"**{i+1}**\n\n🔴 -", unsafe_allow_html=True)
        elif result == 'T':
            st.markdown(f"**{i+1}**\n\n🟡 0", unsafe_allow_html=True)
        else:
            st.markdown(f"**{i+1}**\n\n⚪ _", unsafe_allow_html=True)

# Back 9 display
back_cols = st.columns(9)
for i, col in enumerate(back_cols):
    with col:
        result = st.session_state.back_9[i]
        if result == 'W':
            st.markdown(f"**{i+10}**\n\n🟢 +", unsafe_allow_html=True)
        elif result == 'L':
            st.markdown(f"**{i+10}**\n\n🔴 -", unsafe_allow_html=True)
        elif result == 'T':
            st.markdown(f"**{i+10}**\n\n🟡 0", unsafe_allow_html=True)
        else:
            st.markdown(f"**{i+10}**\n\n⚪ _", unsafe_allow_html=True)

# Calculate results
front_result = calculate_nine(st.session_state.front_9, 'Front 9')
back_result = calculate_nine(st.session_state.back_9, 'Back 9')

# Display results
st.markdown("---")
st.markdown("### Results")

# Create results dataframe
results_data = []

if front_result['details']:
    st.markdown("**Front 9:**")
    
    # Show breakdown
    st.markdown(f"- Net holes won/lost: **{front_result['holes_won']:+d} points**")
    
    for detail in front_result['details']:
        results_data.append({
            'Nine': 'Front 9',
            'Bet': detail['bet'],
            'Holes': detail['holes'],
            'Results': detail['results'],
            'Score': detail['score'],
            'Outcome': detail['outcome'],
            'Points': f"{detail['points']:+d}"
        })
    
    df_front = pd.DataFrame([d for d in results_data if d['Nine'] == 'Front 9'])
    st.dataframe(df_front[['Bet', 'Holes', 'Results', 'Score', 'Outcome', 'Points']], hide_index=True, use_container_width=True)
    
    st.markdown(f"- Bet points: **{front_result['bet_points']:+d} points**")
    st.markdown(f"**Front 9 Total: {front_result['points']} points = ${front_result['points'] * bet_amount:+.0f}**")

if back_result['details']:
    st.markdown("**Back 9:**")
    
    # Show breakdown
    st.markdown(f"- Net holes won/lost: **{back_result['holes_won']:+d} points**")
    
    for detail in back_result['details']:
        results_data.append({
            'Nine': 'Back 9',
            'Bet': detail['bet'],
            'Holes': detail['holes'],
            'Results': detail['results'],
            'Score': detail['score'],
            'Outcome': detail['outcome'],
            'Points': f"{detail['points']:+d}"
        })
    
    df_back = pd.DataFrame([d for d in results_data if d['Nine'] == 'Back 9'])
    st.dataframe(df_back[['Bet', 'Holes', 'Results', 'Score', 'Outcome', 'Points']], hide_index=True, use_container_width=True)
    
    st.markdown(f"- Bet points: **{back_result['bet_points']:+d} points**")
    st.markdown(f"**Back 9 Total: {back_result['points']} points = ${back_result['points'] * bet_amount:+.0f}**")

# Overall 18
if all(h is not None for h in st.session_state.front_9) and all(h is not None for h in st.session_state.back_9):
    overall_points = calculate_overall(st.session_state.front_9, st.session_state.back_9)
    st.markdown(f"**Overall 18: {overall_points} point = ${overall_points * bet_amount:+.0f}**")
    
    total_money = (front_result['points'] + back_result['points'] + overall_points) * bet_amount
    st.markdown("---")
    st.markdown(f"### 💰 TOTAL: ${total_money:+.0f}")

# Instructions
with st.expander("📖 How to Use"):
    st.markdown("""
    1. Set your bet amount at the top
    2. Navigate through holes using Previous/Next buttons
    3. Record each hole result: + (Win), 0 (Tie), - (Loss)
    4. The app automatically:
       - Triggers presses when any bet reaches 2 up/down
       - Adds auto-press on hole 9/18 if last bet is 1 up/down
       - Calculates all points and money
    5. Reset button clears all scores
    
    **Scoring System:**
    - Count total holes won minus holes lost across all 9 holes
    - Add/subtract 1 point for each bet (Original, Presses, Auto-press):
      - Win the bet = +1 point
      - Lose the bet = -1 point
      - Tie the bet = 0 points
    - Total points = (Net holes) + (Bet points)
    
    **Press Rules:**
    - A new press starts when any bet reaches 2 up or 2 down
    - Each press can trigger its own subsequent presses
    - Auto-press on 9/18 only if the last active bet is exactly 1 up or 1 down
    
    **Example:**
    If you win 3 holes, lose 1 hole on the front 9 with 2 presses:
    - Net holes: +2 points
    - Original bet: Won = +1 point
    - Press #1: Won = +1 point
    - Press #2: Lost = -1 point
    - Total: 2 + 1 + 1 + (-1) = 3 points × $5 = $15
    """)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Nassau Golf Scorer - Two Down Auto Press with New Scoring Framework</p>", unsafe_allow_html=True)