from fpdf import FPDF
import os

class ResumePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 20)
        self.cell(0, 10, 'Rahul Sharma', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Backend Software Engineer | Distributed Systems & Cloud Infrastructure', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, 0, 1, 'L', 1)
        self.ln(2)

    def chapter_body(self, text):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 6, text)
        self.ln(4)

pdf = ResumePDF()
pdf.add_page()

# Contact Info
pdf.set_font('Arial', '', 10)
contact_info = "Email: rahul.sharma@gmail.com | Phone: +91 9876543210\nLinkedIn: https://www.linkedin.com/in/rahulsharma-backend | GitHub: https://github.com/rahul-sharma-dev | Portfolio: https://rahulsharma.dev\nLocation: Bengaluru, Karnataka, India"
pdf.multi_cell(0, 5, contact_info, 0, 'C')
pdf.ln(5)

# Professional Summary
pdf.chapter_title('Professional Summary')
pdf.chapter_body(
    "Results-driven Backend Software Engineer with 3 years 8 months of experience designing and building scalable distributed systems. "
    "Proficient in Python, Go, and Java, with extensive hands-on expertise in AWS, Kubernetes, and Docker. "
    "Proven track record of optimizing database performance, implementing event-driven architectures using Kafka, and delivering robust REST APIs. "
    "Passionate about system design, microservices, and solving complex backend engineering challenges."
)

# Experience
pdf.chapter_title('Work Experience')
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 6, 'Razorpay Technologies Pvt Ltd', 0, 1)
pdf.set_font('Arial', 'I', 11)
pdf.cell(0, 6, 'Backend Software Engineer | Jan 2023 - Present', 0, 1)
pdf.chapter_body(
    "- Spearheaded the backend architecture for a high-throughput payment reconciliation microservice using Go and gRPC.\n"
    "- Optimized legacy PostgreSQL database queries, reducing average query execution time by 40%.\n"
    "- Introduced Redis read-through caching to decrease latency for the primary checkout API by 150ms.\n"
    "- Containerized existing monolithic applications using Docker and orchestrated deployments on AWS EKS (Kubernetes).\n"
    "- Mentored two junior developers and conducted code reviews focusing on performance and security."
)

pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 6, 'Swiggy', 0, 1)
pdf.set_font('Arial', 'I', 11)
pdf.cell(0, 6, 'Software Engineer | Aug 2020 - Dec 2022', 0, 1)
pdf.chapter_body(
    "- Developed scalable microservices in Java (Spring Boot) and Python (FastAPI) for the logistics assignment team.\n"
    "- Integrated Apache Kafka to handle asynchronous event processing for real-time delivery tracking, processing 10k+ events/sec.\n"
    "- Built and documented 15+ secure REST APIs for internal operations dashboards.\n"
    "- Collaborated with cross-functional teams to improve order assignment algorithm efficiency by 12%."
)

# Technical Skills
pdf.chapter_title('Technical Skills')
pdf.chapter_body(
    "Languages: Python, Go, Java\n"
    "Frameworks & Libraries: FastAPI, Spring Boot, Flask\n"
    "Databases & Caching: PostgreSQL, MySQL, Redis, MongoDB\n"
    "Cloud & DevOps: AWS (EC2, S3, RDS, EKS), Docker, Kubernetes, CI/CD, Terraform\n"
    "Architecture & Messaging: Microservices, System Design, REST APIs, Apache Kafka, gRPC"
)

# Education
pdf.chapter_title('Education')
pdf.set_font('Arial', 'B', 12)
pdf.cell(0, 6, 'National Institute of Technology (NIT), Trichy', 0, 1)
pdf.set_font('Arial', 'I', 11)
pdf.cell(0, 6, 'Bachelor of Technology in Computer Science | 2016 - 2020', 0, 1)
pdf.ln(4)

# Certifications
pdf.chapter_title('Certifications & Projects')
pdf.chapter_body(
    "- AWS Certified Solutions Architect - Associate\n"
    "- Certified Kubernetes Administrator (CKA)\n"
    "- Distributed Key-Value Store: Built a fault-tolerant distributed key-value store using the Raft consensus algorithm in Go."
)

os.makedirs('/home/aashrith/Dev/CandidateCore/sample_data/test_dataset', exist_ok=True)
pdf.output('/home/aashrith/Dev/CandidateCore/sample_data/test_dataset/resume.pdf')
