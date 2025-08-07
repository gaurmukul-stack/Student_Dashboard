import streamlit as st
import json
from datetime import datetime, timedelta
import time
import pandas as pd
import plotly.express as px
import pytz
import requests
from utils.cgpa_calc import calculate_cgpa
from utils.helpers import get_subject_color, load_data, save_data
import streamlit.components.v1 as components

# Configuration
st.set_page_config(
    page_title="Student Genius Pro",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    with open("assets/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state
if 'tasks' not in st.session_state:
    st.session_state.tasks = load_data("tasks")

if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
    st.session_state.timer_start = None
    st.session_state.timer_duration = 25 * 60  # 25 minutes in seconds

# Menu options
menu = [
    "🏠 Dashboard", 
    "📅 Academic Planner", 
    "📚 Study Hub", 
    "📊 Performance", 
    "✅ Task Manager", 
    "⏳ Focus Timer",
    "📝 Quick Notes"
]

choice = st.sidebar.selectbox("NAVIGATION", menu)

# Dashboard
if choice == "🏠 Dashboard":
    st.title("🎓 Student Genius Pro")
    
    # Time-based greeting
    current_hour = datetime.now(pytz.timezone('Asia/Kolkata')).hour
    greeting = "Good night" if current_hour < 5 else \
               "Good morning" if current_hour < 12 else \
               "Good afternoon" if current_hour < 17 else \
               "Good evening"
    
    # Dashboard layout
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"{greeting}, {st.secrets.get('USER_NAME', 'Student')}!")
        st.markdown("""
        Your all-in-one academic companion with:
        - 📚 Smart study resources
        - ⏳ Productivity tools
        - 📊 Performance tracking
        - ✅ Task management
        """)
    
    with col2:
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        st.metric("📅 Today", now.strftime("%d %b %Y"))
        st.metric("🕒 Current Time", now.strftime("%H:%M:%S"))
    
    # Quick stats
    st.subheader("📊 Your Stats")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        notes = load_data("notes")
        st.metric("📝 Available Notes", len(notes))
    with col2:
        pending = sum(1 for t in st.session_state.tasks if not t.get('completed', False))
        st.metric("✅ Pending Tasks", pending)
    with col3:
        events = load_data("events")
        upcoming = sum(1 for e in events if datetime.strptime(e['date'], "%Y-%m-%d") >= datetime.now())
        st.metric("📅 Upcoming Events", upcoming)
    with col4:
        st.metric("🎯 Productivity Score", f"{min(100, pending*10)}%")

    # Motivational quote
    try:
        response = requests.get("https://api.quotable.io/random?tags=education|motivation")
        if response.status_code == 200:
            quote = response.json()
            st.info(f"💡 **Quote of the Day**: *{quote['content']}* - {quote['author']}")
    except:
        st.info("💡 **Quote**: *Education is the most powerful weapon which you can use to change the world.* - Nelson Mandela")

# Academic Planner
elif choice == "📅 Academic Planner":
    st.title("📅 Academic Planner")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🗓️ Calendar", "📌 Important Dates", "➕ Add Event", "📊 Progress Tracker", "⚙️ Settings"])

    # Initialize session state for events if not exists
    if 'events' not in st.session_state:
        st.session_state.events = load_data("events")
    
    with tab1:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Interactive Calendar")
        with col2:
            view_option = st.selectbox("View Mode", ["Monthly", "Weekly", "Daily"], index=0)
        
        if view_option == "Monthly":
            # Enhanced calendar view with interactive elements
            calendar_html = """
            <div id='calendar'></div>
            <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.css' rel='stylesheet'>
            <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.11.3/main.min.js'></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var calendarEl = document.getElementById('calendar');
                    var calendar = new FullCalendar.Calendar(calendarEl, {
                        initialView: 'dayGridMonth',
                        headerToolbar: {
                            left: 'prev,next today',
                            center: 'title',
                            right: 'dayGridMonth,timeGridWeek,timeGridDay'
                        },
                        events: """ + json.dumps([{
                            'title': e['title'],
                            'start': e['date'],
                            'description': e.get('description', ''),
                            'color': '#4285F4' if 'exam' in e['title'].lower() else '#34A853'
                        } for e in st.session_state.events]) + """,
                        eventClick: function(info) {
                            const eventDesc = info.event.extendedProps.description;
                            const eventDate = info.event.start.toLocaleDateString();
                            alert(info.event.title + '\\n' + eventDate + '\\n\\n' + eventDesc);
                        }
                    });
                    calendar.render();
                });
            </script>
            """
            components.html(calendar_html, height=600)
            
        elif view_option == "Weekly":
            st.image("https://via.placeholder.com/800x400?text=Weekly+View+with+Time+Slots", use_column_width=True)
        else:
            selected_date = st.date_input("Select Date", datetime.now())
            st.write(f"### Schedule for {selected_date.strftime('%A, %B %d, %Y')}")
            daily_events = [e for e in st.session_state.events if e['date'] == selected_date.strftime("%Y-%m-%d")]
            
            if not daily_events:
                st.info("No events scheduled for this day")
            else:
                for event in daily_events:
                    with st.expander(f"⏰ {event['time'] if 'time' in event else 'All Day'} - {event['title']}"):
                        st.write(event.get('description', ''))
                        if 'location' in event:
                            st.write(f"📍 {event['location']}")
                        if 'link' in event:
                            st.markdown(f"[🔗 Event Link]({event['link']})")
                        if st.button("Delete", key=f"del_{event['date']}_{event['title']}"):
                            st.session_state.events.remove(event)
                            st.rerun()
    
    with tab2:
        st.subheader("Upcoming Events")
        
        # Filter and sorting options
        col1, col2 = st.columns(2)
        with col1:
            sort_option = st.selectbox("Sort by", ["Date", "Priority", "Title"], index=0)
        with col2:
            filter_option = st.multiselect("Filter by type", ["Exam", "Assignment", "Lecture", "Other"], default=["Exam", "Assignment"])
        
        # Priority tagging and filtering
        for event in st.session_state.events:
            if 'priority' not in event:
                event['priority'] = "Medium"
        
        sorted_events = sorted(st.session_state.events, key=lambda x: (
            datetime.strptime(x['date'], "%Y-%m-%d"),
            {"High": 0, "Medium": 1, "Low": 2}[x['priority']]
        ))
        
        for event in sorted_events:
            event_date = datetime.strptime(event['date'], "%Y-%m-%d")
            days_left = (event_date - datetime.now()).days
            
            # Skip past events and apply filters
            if days_left >= 0 and (not filter_option or any(ft.lower() in event['title'].lower() for ft in filter_option)):
                with st.container(border=True):
                    # Color code based on priority
                    border_color = "#FF0000" if event['priority'] == "High" else "#FFA500" if event['priority'] == "Medium" else "#008000"
                    st.markdown(f"""<style> div[data-testid="stVerticalBlockBorderWrapper"] {{ border-left: 5px solid {border_color}; }} </style>""", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([1, 4, 1])
                    with col1:
                        st.markdown(f"**{event_date.strftime('%d %b')}**")
                        st.caption(f"{'⏰' if 'time' in event else '📅'} {days_left}d")
                    with col2:
                        st.subheader(event['title'])
                        st.caption(event.get('description', ''))
                        if event.get('link'):
                            st.markdown(f"[More info]({event['link']})")
                        if 'location' in event:
                            st.caption(f"📍 {event['location']}")
                    with col3:
                        with st.popover("⚙️"):
                            new_priority = st.selectbox(
                                "Priority", 
                                ["High", "Medium", "Low"], 
                                index=["High", "Medium", "Low"].index(event['priority']),
                                key=f"priority_{event['date']}_{event['title']}"
                            )
                            if new_priority != event['priority']:
                                event['priority'] = new_priority
                                st.rerun()
                            
                            if st.button("Delete", key=f"delete_{event['date']}_{event['title']}"):
                                st.session_state.events.remove(event)
                                st.rerun()
    
    with tab3:
        st.subheader("Add New Event")
        
        with st.form("add_event_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                event_title = st.text_input("Event Title*", placeholder="Final Exam")
                event_date = st.date_input("Date*", min_value=datetime.now())
                event_time = st.time_input("Time (optional)")
            with col2:
                event_type = st.selectbox("Type", ["Exam", "Assignment", "Lecture", "Meeting", "Other"])
                priority = st.select_slider("Priority", ["High", "Medium", "Low"], value="Medium")
            
            event_desc = st.text_area("Description", placeholder="Add details about the event...")
            event_link = st.text_input("Link (optional)", placeholder="https://")
            event_location = st.text_input("Location (optional)", placeholder="Room 101 or Zoom link")
            
            submitted = st.form_submit_button("Add Event")
            if submitted:
                if not event_title:
                    st.error("Title is required!")
                else:
                    new_event = {
                        'title': event_title,
                        'date': event_date.strftime("%Y-%m-%d"),
                        'type': event_type,
                        'priority': priority,
                        'description': event_desc
                    }
                    if event_time:
                        new_event['time'] = event_time.strftime("%H:%M")
                    if event_link:
                        new_event['link'] = event_link
                    if event_location:
                        new_event['location'] = event_location
                    
                    st.session_state.events.append(new_event)
                    st.success("Event added successfully!")
                    st.balloons()
    
with tab4:
    st.subheader("Academic Progress Tracker")
    
    # Course management
    st.write("### Course Management")
    courses = load_data("courses")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_course = st.selectbox("Select Course", [c['name'] for c in courses] + ["Add New Course"])
    with col2:
        if selected_course == "Add New Course":
            with st.popover("➕ New Course"):
                with st.form("add_course"):
                    course_name = st.text_input("Course Name")
                    course_code = st.text_input("Course Code")
                    credit_hours = st.number_input("Credit Hours", min_value=1, max_value=5, value=3)
                    if st.form_submit_button("Add"):
                        courses.append({
                            'name': course_name,
                            'code': course_code,
                            'credits': credit_hours
                        })
                        st.rerun()
    
    if selected_course and selected_course != "Add New Course":
        course = next((c for c in courses if c['name'] == selected_course), None)
        if course:
            st.write(f"**Course Code:** {course['code']} | **Credits:** {course['credits']}")
            
            # Grade tracker
            st.write("### Grade Calculator")
            col1, col2, col3 = st.columns(3)
            with col1:
                assignments = st.number_input("Assignments Score", min_value=0, max_value=100, value=85)
            with col2:
                midterm = st.number_input("Midterm Score", min_value=0, max_value=100, value=75)
            with col3:
                final = st.number_input("Final Exam Score", min_value=0, max_value=100, value=80)
            
            weights = {
                'assignments': 0.4,
                'midterm': 0.3,
                'final': 0.3
            }
            
            total_score = (assignments * weights['assignments'] + 
                         midterm * weights['midterm'] + 
                         final * weights['final'])
            
            st.metric("Overall Grade", f"{total_score:.1f}%", 
                     help="Weights: Assignments 40%, Midterm 30%, Final 30%")
            
            # Progress visualization
            st.write("### Progress Overview")
            progress_data = pd.DataFrame({
                'Component': ['Assignments', 'Midterm', 'Final'],
                'Score': [assignments, midterm, final],
                'Target': [90, 80, 80]
            })
            
            # Visualization with fallback
            try:
                fig = px.bar(progress_data, x='Component', y=['Score', 'Target'], 
                            barmode='group', title="Performance vs Targets")
                st.plotly_chart(fig, use_container_width=True)
            except NameError:  # If plotly not available
                st.bar_chart(progress_data.set_index('Component'))
                st.write("*Install plotly for enhanced visualizations*")
# Study Hub
elif choice == "📚 Study Hub":
    st.title("📚 Study Hub")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Notes", "📚 Books", "🎥 Videos", "➕ Add Resource"])
    
    with tab1:
        st.subheader("Course Notes")
        try:
            notes = load_data("notes")
        except:
            notes = {}
            st.warning("Could not load notes data. Initializing empty notes collection.")
        
        search_term = st.text_input("🔍 Search Notes", "")
        sort_option = st.selectbox("Sort By", ["Subject A-Z", "Recent First", "Course Code"])
        
        # Display notes in responsive grid
        cols = st.columns(2)
        notes_to_display = []
        
        for subject, note_data in notes.items():
            if search_term.lower() in subject.lower():
                notes_to_display.append((subject, note_data))
        
        # Sorting logic
        if sort_option == "Recent First":
            notes_to_display.sort(key=lambda x: x[1].get('date', ''), reverse=True)
        elif sort_option == "Course Code":
            notes_to_display.sort(key=lambda x: x[1].get('code', ''))
        else:  # Default A-Z
            notes_to_display.sort(key=lambda x: x[0])
        
        # Display notes
        for i, (subject, note_data) in enumerate(notes_to_display):
            color = get_subject_color(subject)
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"<h4 style='color: {color}'>{subject}</h4>", unsafe_allow_html=True)
                    st.caption(f"📅 {note_data.get('date', 'No date')} | 🏷️ {note_data.get('tags', '')}")
                    st.write(note_data.get('description', 'Study notes available'))
                    
                    if "link" in note_data:
                        st.download_button(
                            label="Download PDF",
                            data=note_data["link"],
                            file_name=f"{subject.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.warning("No file attached")
                    
                    if st.button("Delete", key=f"del_note_{subject}"):
                        del notes[subject]
                        save_data("notes", notes)
                        st.rerun()
    
    with tab2:
        st.subheader("Recommended Books")
        # Similar structure for books tab
        # ...
    
    with tab3:
        st.subheader("Educational Videos")
        # Similar structure for videos tab
        # ...
    
    with tab4:
        st.subheader("Add New Resource")
        with st.form("add_resource"):
            resource_type = st.selectbox("Resource Type", ["Notes", "Book", "Video"])
            name = st.text_input("Resource Name")
            description = st.text_area("Description")
            link = st.text_input("URL/Link")
            date = st.date_input("Date", datetime.now())
            
            if st.form_submit_button("Add Resource"):
                new_resource = {
                    "name": name,
                    "description": description,
                    "link": link,
                    "date": date.strftime("%Y-%m-%d"),
                    "type": resource_type
                }
                
                # Save based on type
                if resource_type == "Notes":
                    notes[name] = new_resource
                    save_data("notes", notes)
                # Similar for other types
                
                st.success("Resource added successfully!")
                st.balloons()
# Performance Tracker
elif choice == "📊 Performance":
    st.title("📊 Academic Performance")
    
    tab1, tab2 = st.tabs(["📈 CGPA Calculator", "📚 Subject Analysis"])
    
    with tab1:
        st.subheader("CGPA Calculator")
        
        semesters = st.number_input("Number of semesters:", min_value=1, max_value=10, value=1)
        
        grades = []
        credits = []
        
        for i in range(semesters):
            with st.expander(f"Semester {i+1}", expanded=(i==0)):
                col1, col2 = st.columns(2)
                with col1:
                    grades.append(st.number_input(
                        f"GPA for Semester {i+1}:",
                        min_value=0.0, max_value=10.0, step=0.01,
                        key=f"gpa_{i}"
                    ))
                with col2:
                    credits.append(st.number_input(
                        f"Credits for Semester {i+1}:",
                        min_value=1, max_value=30, step=1,
                        key=f"credits_{i}"
                    ))
        
        if st.button("Calculate CGPA"):
            if len(grades) == semesters and len(credits) == semesters:
                result = calculate_cgpa(grades, credits)
                
                st.subheader("Results")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Your CGPA", f"{result:.2f}")
                with col2:
                    st.progress(result/10.0)
                
                # Performance analysis
                if result >= 9.0:
                    st.success("🌟 Excellent! You're in the top percentile.")
                elif result >= 8.0:
                    st.success("👍 Very Good! Keep up the good work.")
                elif result >= 7.0:
                    st.info("💪 Good. You're doing well but can improve.")
                else:
                    st.warning("📌 Needs improvement. Focus on weak areas.")

# Task Manager
elif choice == "✅ Task Manager":
    st.title("✅ Smart Task Manager")
    
    # Initialize tasks with proper structure if not in session state
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    
    # Add task form
    with st.form("add_task_form"):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_task = st.text_input("✏️ Task description", placeholder="What needs to be done?")
        with col2:
            priority = st.selectbox("Priority", ["🔴 High", "🟡 Medium", "🟢 Low"])
        
        due_date = st.date_input("Due date", min_value=datetime.now().date())
        submitted = st.form_submit_button("➕ Add Task")
        
        if submitted and new_task:
            task_obj = {
                "task": new_task,
                "priority": priority,
                "due_date": due_date.strftime("%Y-%m-%d"),  # Ensure consistent date format
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "completed": False
            }
            st.session_state.tasks.append(task_obj)
            save_data("tasks", st.session_state.tasks)
            st.success("Task added!")
            st.rerun()
    
    # Task list
    st.markdown("---")
    st.subheader("📋 Your Tasks")
    
    if not st.session_state.tasks:
        st.info("No tasks yet. Add some tasks to get started!")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_completed = st.checkbox("Show completed tasks", value=False)
        with col2:
            sort_by = st.selectbox("Sort by", ["Priority", "Due Date"])
        
        # Filter tasks and handle missing due_date
        filtered_tasks = []
        for t in st.session_state.tasks:
            if show_completed or not t.get('completed', False):
                # Add default due_date if missing
                if 'due_date' not in t:
                    t['due_date'] = datetime.now().strftime("%Y-%m-%d")
                filtered_tasks.append(t)
        
        # Sort tasks with error handling
        try:
            if sort_by == "Priority":
                priority_order = {"🔴 High": 0, "🟡 Medium": 1, "🟢 Low": 2}
                filtered_tasks.sort(key=lambda x: priority_order[x.get('priority', '🟢 Low')])
            else:
                filtered_tasks.sort(key=lambda x: x.get('due_date', datetime.now().strftime("%Y-%m-%d")))
        except Exception as e:
            st.error(f"Error sorting tasks: {e}")
        
        # Display tasks with proper error handling
        for i, task in enumerate(filtered_tasks):
            task_key = f"task_{i}"
            with st.container(border=True):
                col1, col2 = st.columns([1, 20])
                with col1:
                    completed = st.checkbox(
                        "", 
                        value=task.get('completed', False), 
                        key=f"complete_{task_key}",
                        on_change=lambda i=i: toggle_task_completion(i)
                    )
                with col2:
                    # Safely get task properties with defaults
                    task_text = task.get('task', 'Untitled task')
                    task_priority = task.get('priority', '🟢 Low')
                    
                    if task.get('completed', False):
                        st.markdown(f"<s>{task_priority} {task_text}</s>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{task_priority} {task_text}**")
                    
                    # Handle due date with proper error checking
                    try:
                        due_date_str = task.get('due_date', datetime.now().strftime("%Y-%m-%d"))
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        days_left = (due_date - datetime.now().date()).days
                        
                        if days_left < 0:
                            status = f"❌ Overdue by {-days_left} days"
                        elif days_left == 0:
                            status = "⚠️ Due today"
                        elif days_left <= 3:
                            status = f"⚠️ Due in {days_left} days"
                        else:
                            status = f"📅 Due in {days_left} days"
                    except Exception as e:
                        status = "⚠️ Date error"
                        st.error(f"Error processing date for task: {e}")
                    
                    created_time = task.get('created', 'Unknown time')
                    st.caption(f"{status} | Created: {created_time}")
                
                if st.button("🗑️", key=f"delete_{task_key}"):
                    try:
                        # Find the actual index in the original tasks list
                        original_index = next((idx for idx, t in enumerate(st.session_state.tasks) 
                                            if t.get('created', '') == task.get('created', '')), None)
                        if original_index is not None:
                            st.session_state.tasks.pop(original_index)
                            save_data("tasks", st.session_state.tasks)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting task: {e}")
# Focus Timer
elif choice == "⏳ Focus Timer":
    st.title("⏳ Focus Timer")
    
    tab1, tab2 = st.tabs(["🍅 Pomodoro", "⏱️ Custom Timer"])
    
    # Initialize session state
    if 'timer_running' not in st.session_state:
        st.session_state.update({
            'timer_running': False,
            'timer_type': None,
            'timer_start': None,
            'timer_duration': 0,
            'last_update': None
        })
    
    with tab1:
        st.subheader("Pomodoro Timer")
        st.markdown("""
        The Pomodoro Technique:
        1. Work for 25 minutes
        2. Take a 5-minute break
        3. Repeat, with longer breaks after 4 sessions
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Pomodoro (25 min)"):
                st.session_state.update({
                    'timer_running': True,
                    'timer_start': datetime.now(),
                    'timer_duration': 25 * 60,
                    'timer_type': "Pomodoro",
                    'last_update': datetime.now()
                })
        
        with col2:
            if st.button("Stop Timer"):
                if st.session_state.timer_running:
                    elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
                    st.info(f"Stopped after {int(elapsed//60)} min {int(elapsed%60)} sec")
                st.session_state.timer_running = False
        
        # Timer display
        pomodoro_display = st.empty()
        
        if st.session_state.timer_running and st.session_state.timer_type == "Pomodoro":
            elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
            remaining = max(0, st.session_state.timer_duration - elapsed)
            
            minutes, seconds = divmod(int(remaining), 60)
            progress = min(1.0, elapsed / st.session_state.timer_duration)
            
            pomodoro_display.progress(progress, text=f"⏳ {minutes:02d}:{seconds:02d} remaining")
            
            if remaining <= 0:
                st.balloons()
                st.success("Time's up! Take a 5-minute break.")
                st.session_state.timer_running = False
                pomodoro_display.empty()
            else:
                time.sleep(0.1)
                st.rerun()
    
    with tab2:
        st.subheader("Custom Timer")
        
        col1, col2 = st.columns(2)
        with col1:
            custom_minutes = st.number_input("Minutes", min_value=0, max_value=120, value=25)
        with col2:
            custom_seconds = st.number_input("Seconds", min_value=0, max_value=59, value=0)
        
        total_seconds = custom_minutes * 60 + custom_seconds
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Custom Timer"):
                if total_seconds > 0:
                    st.session_state.update({
                        'timer_running': True,
                        'timer_start': datetime.now(),
                        'timer_duration': total_seconds,
                        'timer_type': "Custom",
                        'last_update': datetime.now()
                    })
                else:
                    st.warning("Please set a valid time duration")
        
        with col2:
            if st.button("Stop Custom Timer"):
                if st.session_state.timer_running:
                    elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
                    st.info(f"Stopped after {int(elapsed//60)} min {int(elapsed%60)} sec")
                st.session_state.timer_running = False
        
        # Timer display
        custom_display = st.empty()
        
        if st.session_state.timer_running and st.session_state.timer_type == "Custom":
            elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
            remaining = max(0, st.session_state.timer_duration - elapsed)
            
            minutes, seconds = divmod(int(remaining), 60)
            progress = min(1.0, elapsed / st.session_state.timer_duration)
            
            custom_display.progress(progress, text=f"⏳ {minutes:02d}:{seconds:02d} remaining")
            
            if remaining <= 0:
                st.balloons()
                st.success("Custom timer completed!")
                st.session_state.timer_running = False
                custom_display.empty()
            else:
                time.sleep(0.1)
                st.rerun()
# Quick Notes
elif choice == "📝 Quick Notes":
    st.title("📝 Quick Notes")
    
    notes = load_data("quick_notes")
    current_note = st.text_area("Write your note here:", height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Note"):
            if current_note.strip():
                notes.append({
                    "content": current_note,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_data("quick_notes", notes)
                st.success("Note saved!")
    with col2:
        if st.button("🧹 Clear"):
            current_note = ""
    
    st.markdown("---")
    st.subheader("📋 Saved Notes")
    
    for i, note in enumerate(notes):
        with st.expander(f"Note {i+1} - {note['timestamp']}"):
            st.write(note['content'])
            if st.button(f"Delete Note {i+1}", key=f"delete_note_{i}"):
                notes.pop(i)
                save_data("quick_notes", notes)
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div class='footer'>
    <p>🎓 Student Genius Pro v2.0 | Made with Streamlit</p>
    <p>📅 Last updated: {}</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)

def toggle_task_completion(index):
    st.session_state.tasks[index]['completed'] = not st.session_state.tasks[index]['completed']
    save_data("tasks", st.session_state.tasks)