"""
Pure local data generator - no API calls needed.
Generates 25,000+ English + 25,000+ Russian examples with rich, varied content.
"""
import json
import random
import time
import sys
import os
import threading
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# Progress bar system
# ============================================================

class AgentProgress:
    def __init__(self):
        self.agents = {}
        self.lock = threading.Lock()
        self.running = True

    def register(self, agent_id, model, api, total_steps=100):
        with self.lock:
            self.agents[agent_id] = {
                "model": model, "api": api,
                "current": 0, "total": total_steps,
                "status": "waiting", "result_count": 0
            }

    def update(self, agent_id, current, status="", result_count=None):
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]["current"] = current
                if status: self.agents[agent_id]["status"] = status
                if result_count is not None: self.agents[agent_id]["result_count"] = result_count

    def complete(self, agent_id, result_count=0):
        with self.lock:
            if agent_id in self.agents:
                self.agents[agent_id]["current"] = self.agents[agent_id]["total"]
                self.agents[agent_id]["status"] = "done"
                self.agents[agent_id]["result_count"] = result_count

    def render(self):
        with self.lock:
            lines = []
            lines.append("\033[H\033[J")
            lines.append("=" * 70)
            lines.append("  SwimeGPT-K1.2  |  Data Generation Progress")
            lines.append("=" * 70)
            lines.append("")
            for aid, info in sorted(self.agents.items()):
                pct = info["current"] / max(info["total"], 1)
                filled = int(pct * 16)
                bar = "#" * filled + "-" * (16 - filled)
                status_icon = "[OK]" if info["status"] == "done" else "[>>]" if info["status"] == "generating" else "[..]"
                line = f"  [{bar}] {status_icon} {info['model']:<22} | {info['api']:<16} | {info['status']:<12} | {info['result_count']} items"
                lines.append(line)
            lines.append("")
            total = sum(a["result_count"] for a in self.agents.values())
            lines.append(f"  Total items collected: {total}")
            lines.append("=" * 70)
            sys.stdout.write("\n".join(lines))
            sys.stdout.flush()

    def stop(self):
        self.running = False

progress = AgentProgress()

def render_loop():
    while progress.running:
        progress.render()
        time.sleep(0.3)

# ============================================================
# Rich English content templates
# ============================================================

EN_PROGRAMMING_TEMPLATES = [
    "In Python, a {concept} is used to {action}. For example, you can define a {concept} using the '{keyword}' keyword. This allows developers to {benefit}. Here's how it works: first, you declare the {concept}, then you implement the logic, and finally you call it when needed. The {concept} pattern is fundamental to writing clean, maintainable code that other developers can easily understand and modify.",
    "Understanding {concept} is essential for any programmer. When you use {concept}, you can {action} more efficiently. The key advantage is that it provides {benefit}. Many modern programming languages support this feature, including Python, JavaScript, and C++. Let's explore a practical example: imagine you need to process a large dataset. Using {concept}, you can accomplish this task with minimal code while maintaining readability.",
    "The {concept} design pattern helps developers {action} in a structured way. This pattern is particularly useful when you need to {benefit}. In object-oriented programming, {concept} promotes code reusability and maintainability. Consider a scenario where you're building a web application: implementing {concept} can significantly reduce code duplication and improve the overall architecture of your project.",
    "When working with {concept}, it's important to understand the underlying principles. The main idea is to {action} while maintaining {benefit}. This approach is widely used in software engineering because it simplifies complex operations. For instance, in a database application, {concept} can help manage connections efficiently, reducing the risk of resource leaks and improving overall system stability.",
    "{concept} is one of the most powerful features in modern programming. It enables you to {action} with ease. The primary benefit is {benefit}, which makes your code more robust and scalable. Professional developers use {concept} daily to build reliable applications. Learning this concept will significantly improve your programming skills and help you write more elegant solutions.",
    "A common use case for {concept} is when you need to {action}. The implementation typically involves creating a {concept} that handles the core logic. By following best practices, you can ensure {benefit} throughout your codebase. Many frameworks provide built-in support for {concept}, making it easier to integrate into existing projects without major refactoring.",
    "The evolution of {concept} in programming languages has been remarkable. Early implementations were basic, but modern {concept} features provide {benefit} that were unimaginable decades ago. Today, developers can {action} using sophisticated tools and libraries. Understanding the history of {concept} helps appreciate why certain design decisions were made and how to use them effectively.",
    "Debugging issues related to {concept} requires a systematic approach. First, identify where the {concept} is being used. Then, trace the flow of data to understand how {action} is performed. Common mistakes include forgetting to handle edge cases, which can compromise {benefit}. Using a debugger and adding logging statements can help pinpoint the exact source of the problem.",
    "Performance optimization often involves improving how {concept} is implemented. By analyzing bottlenecks, developers can {action} more efficiently. Techniques include caching results, reducing unnecessary computations, and leveraging {benefit} to minimize resource consumption. These optimizations can lead to significant speed improvements, especially in applications that process large amounts of data.",
    "Testing {concept} implementations requires careful consideration of edge cases. Unit tests should verify that {action} works correctly under various conditions. Integration tests ensure that {concept} interacts properly with other components. Achieving {benefit} through comprehensive testing gives confidence that the code will behave predictably in production environments.",
]

EN_SCIENCE_TEMPLATES = [
    "The concept of {concept} in {field} has revolutionized our understanding of {topic}. Scientists have discovered that {concept} plays a crucial role in {action}. Recent research shows that when {concept} is applied correctly, it can lead to significant {benefit}. This discovery has opened new avenues for exploration in {field} and may eventually transform how we approach related challenges.",
    "In the field of {field}, {concept} represents a fundamental principle. Researchers study {concept} to better understand how {topic} works. The implications of this research are far-reaching, affecting everything from {action} to {benefit}. Understanding {concept} is essential for anyone studying {field}, as it forms the basis for more advanced topics and practical applications.",
    "The study of {concept} has been a cornerstone of {field} for decades. Through careful observation and experimentation, scientists have determined that {concept} directly influences {topic}. This relationship is critical because it helps explain {action}. Furthermore, the practical applications of {concept} continue to expand, offering new {benefit} that improve our daily lives.",
    "{concept} in {field} demonstrates the interconnectedness of natural systems. When researchers examine {topic}, they find that {concept} is a key factor in {action}. This understanding has led to breakthrough treatments and technologies that provide {benefit}. The ongoing study of {concept} promises even more discoveries that could reshape our understanding of the natural world.",
    "Modern {field} relies heavily on understanding {concept}. By analyzing {topic}, scientists can predict {action} with remarkable accuracy. This predictive power has numerous applications, from improving {benefit} to developing new technologies. The study of {concept} continues to push the boundaries of human knowledge and inspires new generations of researchers.",
    "The mathematical foundations of {concept} provide a rigorous framework for understanding {topic}. Equations describing {concept} allow scientists to model {action} with precision. These models have been validated through extensive experimentation, confirming that {benefit} can be achieved through careful application of theoretical principles. The interplay between theory and experiment drives progress in {field}.",
    "Educational programs in {field} increasingly emphasize the importance of {concept}. Students learn how {concept} relates to {topic} through hands-on experiments and theoretical coursework. This dual approach ensures that graduates can both understand the principles behind {action} and apply them to achieve {benefit} in real-world situations. The demand for such expertise continues to grow.",
    "International collaboration has accelerated research into {concept}. Scientists from different countries share data about {topic}, enabling larger studies than any single institution could conduct. This cooperative approach has revealed that {action} is more complex than previously thought, leading to refined theories about {benefit}. The global nature of modern science makes such collaboration essential.",
    "The practical applications of {concept} extend far beyond academic research. Industries ranging from healthcare to technology rely on insights from {field} to {action}. Companies that understand {concept} can develop products that provide {benefit} to consumers. This translation of scientific knowledge into practical solutions demonstrates the real-world value of fundamental research.",
    "Future directions in {field} research include exploring new aspects of {concept}. Scientists are investigating how {topic} might be manipulated to {action} more effectively. Early results suggest that {benefit} could be significantly improved through novel approaches. These investigations require interdisciplinary collaboration, combining expertise from multiple fields to tackle complex questions.",
]

EN_TECHNICAL_TEMPLATES = [
    "Technical documentation for {concept}: This component is designed to {action} within a larger system. The primary interface exposes methods for {benefit}. Configuration is handled through a settings object that accepts parameters for customization. Error handling is built-in, with appropriate exceptions thrown when invalid states are detected. Usage example: initialize the component, configure settings, then call the main method to {action}.",
    "API Reference: {concept} provides a clean interface for {action}. The main class exposes the following methods: initialize() sets up the internal state, process() performs the core {action}, and finalize() cleans up resources. Each method returns a status object indicating success or failure. The {concept} module is thread-safe and can be used in concurrent environments for {benefit}.",
    "Architecture Overview: The {concept} system follows a layered architecture pattern. The presentation layer handles user interaction, the business logic layer implements {action}, and the data access layer manages persistence. This separation of concerns ensures that changes to one layer don't affect others. The system supports {benefit} through configurable plugins that extend functionality.",
    "Implementation Guide: To implement {concept}, follow these steps. First, define the interface that specifies the contract for {action}. Second, create a concrete implementation that fulfills this contract. Third, write unit tests to verify correct behavior. Finally, integrate the implementation into your application. This approach ensures {benefit} and maintainability throughout the development lifecycle.",
    "Best Practices for {concept}: Always validate input before {action}. Use appropriate error handling to catch and report issues. Document your code thoroughly so other developers can understand the implementation. Follow established naming conventions and coding standards. Test edge cases to ensure robustness. These practices lead to {benefit} in production environments and reduce maintenance costs.",
    "Performance Considerations: When deploying {concept} in production, monitor resource usage carefully. The component should {action} within acceptable latency thresholds. If performance degrades, consider optimizing the implementation or scaling horizontally. Caching strategies can provide {benefit} by reducing redundant computations. Load testing should be performed before deployment to identify potential bottlenecks.",
    "Security Guidelines: The {concept} component must follow security best practices. All inputs should be sanitized before {action} to prevent injection attacks. Authentication and authorization checks should be performed at every layer. Sensitive data must be encrypted both in transit and at rest. Regular security audits help ensure {benefit} and protect against emerging threats.",
    "Migration Guide: When upgrading from a previous version of {concept}, review the changelog carefully. Breaking changes may affect how you {action}. The migration process typically involves updating configuration files, modifying API calls, and running database migrations. Testing in a staging environment before production deployment ensures {benefit} and minimizes downtime during the upgrade process.",
    "Troubleshooting: Common issues with {concept} include configuration errors, resource exhaustion, and compatibility problems. When {action} fails, check the logs for detailed error messages. Verify that all dependencies are installed correctly and that configuration parameters are valid. The community forum provides additional support, and the documentation includes a comprehensive FAQ section for {benefit}.",
    "Integration Patterns: {concept} can be integrated with various external systems. The most common pattern involves using {concept} to {action} while maintaining {benefit}. Adapter patterns help bridge differences between systems, while event-driven architectures enable loose coupling. Choosing the right integration pattern depends on your specific requirements and the constraints of your existing infrastructure.",
]

EN_MATH_TEMPLATES = [
    "The mathematical concept of {concept} is fundamental to understanding {topic}. In its simplest form, {concept} describes the relationship between {action} and {benefit}. This relationship can be expressed using the formula f(x) = {concept}(x), where x represents the input variable. Mathematicians have studied {concept} for centuries, and it remains a cornerstone of modern mathematics with applications across numerous fields.",
    "When solving problems involving {concept}, it's helpful to break the problem into smaller steps. First, identify the known variables and the unknown quantity. Second, apply the appropriate {concept} formula. Third, simplify the expression step by step. Finally, verify your answer by substituting it back into the original equation. This systematic approach ensures accuracy and builds problem-solving skills.",
    "The theorem of {concept} states that for any {topic}, there exists a unique solution that satisfies {action}. This theorem has profound implications for {field}, as it guarantees that {benefit} is always achievable. The proof relies on several key lemmas, each building upon the previous result. Understanding this proof deepens one's appreciation for the elegance of mathematics.",
    "In calculus, {concept} plays a central role in understanding rates of change. When we compute the derivative of a function, we're essentially measuring how {action} changes with respect to {topic}. This concept extends to multiple dimensions, where the gradient vector points in the direction of maximum increase. Applications include optimization, physics simulations, and machine learning algorithms.",
    "Linear algebra provides powerful tools for working with {concept}. Matrices and vectors allow us to represent and manipulate {topic} efficiently. The key operations include addition, multiplication, and transformation. These operations form the foundation for {action}, which is essential in computer graphics, data science, and engineering. Mastering {concept} opens doors to advanced topics in applied mathematics.",
    "The history of {concept} stretches back to ancient civilizations. Early mathematicians developed intuitive understanding of {topic} through practical problems involving {action}. Over centuries, these informal ideas were formalized into rigorous mathematical theory. Today, {concept} is taught in schools worldwide, providing students with {benefit} that serve them throughout their academic and professional careers.",
    "Computational methods have transformed how we apply {concept} to real-world problems. Numerical algorithms can approximate solutions to complex equations involving {topic} that would be impossible to solve by hand. These algorithms leverage the properties of {concept} to {action} efficiently. The development of faster computers continues to expand the range of problems that can be tackled using {benefit}.",
    "Statistical applications of {concept} are widespread in modern data analysis. When analyzing datasets, researchers use {concept} to model relationships between variables. Hypothesis testing relies on understanding how {action} affects {topic}. The resulting insights provide {benefit} that inform decision-making in business, healthcare, and public policy. Statistical literacy has become an essential skill in the information age.",
    "Geometric interpretations of {concept} provide intuitive understanding of abstract ideas. Visualizing {topic} in two or three dimensions helps students grasp how {action} transforms shapes and spaces. This visual approach complements algebraic methods and provides {benefit} for learners who think spatially. Interactive software tools make it possible to explore these geometric relationships dynamically.",
    "Advanced topics in mathematics build upon the foundation of {concept}. Abstract algebra generalizes the properties of {topic} to create new mathematical structures. Topology studies how {action} behaves under continuous transformations. These advanced fields provide {benefit} that have surprising applications in physics, computer science, and cryptography. The unity of mathematics reveals connections between seemingly unrelated areas.",
]

EN_DIALOGUE_TEMPLATES = [
    "User: Can you explain how {concept} works? Assistant: Of course! {concept} is a fundamental concept that allows us to {action}. Think of it like a recipe: you have ingredients (inputs), follow steps (processing), and get a dish (output). The key is understanding how each step transforms the data. Would you like me to walk through a specific example? User: Yes, please! Assistant: Great! Let's start with a simple case where we {action}. First, we initialize our variables. Then, we apply {concept} to transform them. The result is {benefit}. Does that make sense?",
    "User: I'm having trouble understanding {concept}. Assistant: No worries! Many people find {concept} challenging at first. Let me break it down into simpler terms. At its core, {concept} is about {action}. Imagine you're organizing a library: you need a system to categorize books, find them quickly, and keep everything organized. {concept} does exactly that for data. User: That analogy helps! Assistant: I'm glad! Now let's look at how this applies to {benefit} in practice.",
    "User: What's the difference between {concept} and {topic}? Assistant: Excellent question! While both relate to {action}, they serve different purposes. {concept} focuses on the structure and organization, while {topic} deals with the behavior and interaction. Think of {concept} as the blueprint and {topic} as the actual building. Both are essential for {benefit}. User: So they complement each other? Assistant: Exactly! In fact, the best solutions often combine both approaches.",
    "User: How do I implement {concept} in my project? Assistant: Good choice! Here's a step-by-step approach. First, identify where {concept} fits in your architecture. Second, create the necessary data structures to support {action}. Third, implement the core logic that handles {benefit}. Fourth, write tests to verify everything works correctly. Finally, integrate it into your main application. User: Should I use a library or build from scratch? Assistant: It depends on your needs.",
    "User: Why is {concept} important in modern software? Assistant: {concept} has become essential because it addresses several key challenges. First, it improves {action} by providing a standardized approach. Second, it enhances {benefit} through better organization. Third, it makes code more maintainable by separating concerns. In today's fast-paced development environment, these advantages are invaluable. User: Are there any downsides? Assistant: Like any tool, it has trade-offs.",
    "User: Can you give me a real-world example of {concept}? Assistant: Sure! Consider a social media platform. When users {action}, the system uses {concept} to organize and display content efficiently. Without {concept}, the platform would struggle with {topic}, leading to poor user experience. By implementing {concept} properly, the platform achieves {benefit}, keeping users engaged and satisfied. User: That's a great example! Assistant: I'm happy to provide more examples if needed.",
    "User: What are common mistakes when using {concept}? Assistant: Great question! The most common mistake is misunderstanding when to {action}. Some developers overuse {concept}, adding unnecessary complexity. Others underuse it, missing opportunities for {benefit}. The key is finding the right balance. Start simple, then add {concept} where it provides clear value. User: How do I know when it's the right time? Assistant: Look for patterns of repetition or complexity that {concept} can simplify.",
    "User: How does {concept} relate to {topic}? Assistant: They're closely connected! {concept} provides the mechanism for {action}, while {topic} defines the context in which it operates. Think of {concept} as the engine and {topic} as the vehicle. Together, they enable {benefit}. Understanding this relationship helps you make better design decisions. User: That clarifies things a lot. Assistant: Perfect! Let me know if you have more questions.",
    "User: Is {concept} difficult to learn? Assistant: It depends on your background. If you're familiar with {action}, you'll find {concept} intuitive. The core ideas are straightforward, but mastering all the details takes practice. I recommend starting with simple examples and gradually increasing complexity. With consistent effort, you'll achieve {benefit} in no time. User: Any recommended resources? Assistant: There are excellent tutorials and interactive exercises available online.",
    "User: How do I test my {concept} implementation? Assistant: Testing {concept} involves several strategies. Unit tests verify that individual components {action} correctly. Integration tests ensure that {concept} works with other parts of the system. Performance tests measure whether {benefit} meets your requirements. I recommend using a testing framework that supports all these types. User: What about edge cases? Assistant: Absolutely! Edge case testing is crucial for robustness.",
]

EN_HISTORY_TEMPLATES = [
    "The history of {concept} dates back to ancient times when early scholars first observed {topic}. Over centuries, our understanding of {concept} has evolved dramatically. Key milestones include the discovery that {action} could be systematically studied, the development of formal methods for {benefit}, and the modern applications we see today. Each era contributed unique insights that built upon previous knowledge.",
    "Throughout history, {concept} has played a pivotal role in shaping {topic}. From the earliest documented uses in ancient civilizations to modern applications, {concept} has continuously evolved. The Renaissance period saw significant advances in understanding {action}, while the Industrial Revolution brought practical applications that provided {benefit}. Today, {concept} remains a vital area of study and innovation.",
    "The evolution of {concept} reflects humanity's quest for knowledge. Early pioneers recognized that {topic} could be understood through systematic observation. This led to the development of methods for {action} that transformed our world. The cumulative knowledge gained over centuries has resulted in {benefit} that we take for granted today. Studying this history helps us appreciate how far we've come.",
    "Historical analysis of {concept} reveals fascinating patterns of discovery and innovation. Each generation of researchers built upon the work of their predecessors, gradually expanding our understanding of {topic}. Key breakthroughs in {action} often came from unexpected directions, demonstrating the value of interdisciplinary thinking. The practical applications of these discoveries have provided {benefit} to society.",
    "The story of {concept} is one of persistent curiosity and ingenuity. From early observations about {topic} to sophisticated modern theories, the journey has been remarkable. Pioneers in the field developed methods for {action} that seemed impossible at the time. Their dedication led to {benefit} that continues to influence our daily lives. Understanding this history enriches our appreciation of modern achievements.",
    "The cultural impact of {concept} extends beyond academic circles. Literature, art, and philosophy have all been influenced by discoveries related to {topic}. Writers and artists have explored how {action} shapes human experience, creating works that provide {benefit} to audiences. This cultural dimension demonstrates that {concept} is not just a technical subject but a fundamental aspect of human civilization.",
    "Biographical studies of key figures in {concept} reveal the human side of scientific progress. Researchers who studied {topic} often faced significant obstacles, from limited resources to skepticism from peers. Their perseverance in pursuing {action} ultimately led to {benefit} that transformed their field. These stories inspire new generations of scientists and remind us that progress requires dedication.",
    "The economic impact of {concept} has been substantial throughout history. Innovations related to {topic} have created entire industries and millions of jobs. The ability to {action} efficiently has driven economic growth and improved living standards. Investments in research and development continue to yield {benefit} that contribute to global prosperity. The economic case for supporting {concept} research remains strong.",
    "Comparative historical analysis shows how different cultures approached {concept}. While Western traditions emphasized {action}, Eastern philosophies often focused on {topic}. These different perspectives complement each other, providing a more complete understanding of {benefit}. Modern scholarship increasingly recognizes the value of integrating diverse cultural approaches to {concept}.",
    "The future of {concept} research builds on centuries of accumulated knowledge. Emerging technologies enable new ways of studying {topic} that were unimaginable to earlier researchers. Computational methods allow scientists to {action} at scales previously impossible. These advances promise {benefit} that will shape the next chapter in the ongoing story of human discovery and innovation.",
]

EN_CONCEPTS = ["function", "class", "variable", "loop", "array", "dictionary", "recursion", "inheritance", "polymorphism", "encapsulation", "abstraction", "interface", "module", "package", "algorithm", "data structure", "database", "API", "framework", "library", "design pattern", "exception", "thread", "process", "memory", "cache", "buffer", "queue", "stack", "tree", "graph", "hash table", "linked list", "binary search", "sorting", "filtering", "mapping", "reducing", "parsing", "compiling", "debugging", "testing", "deployment", "version control", "continuous integration", "microservice", "container", "virtualization", "networking", "protocol"]
EN_ACTIONS = ["process data", "manage resources", "organize information", "execute operations", "transform inputs", "validate conditions", "handle errors", "optimize performance", "store values", "retrieve information", "compute results", "filter records", "sort elements", "merge datasets", "split strings", "encode values", "decode messages", "compress files", "encrypt data", "authenticate users"]
EN_BENEFITS = ["improved efficiency", "better organization", "enhanced security", "reduced complexity", "increased reliability", "faster execution", "lower memory usage", "easier maintenance", "better scalability", "improved readability", "greater flexibility", "stronger type safety", "cleaner architecture", "faster development", "better testing"]
EN_FIELDS = ["physics", "chemistry", "biology", "computer science", "mathematics", "engineering", "psychology", "sociology", "economics", "neuroscience"]
EN_TOPICS = ["natural phenomena", "complex systems", "human behavior", "technological advancement", "scientific discovery", "mathematical relationships", "biological processes", "chemical reactions", "physical laws", "computational models"]
EN_KEYWORDS = ["def", "class", "import", "from", "return", "yield", "async", "await", "try", "except", "for", "while", "if", "else", "lambda", "with", "raise", "assert", "pass", "break"]

EN_TEMPLATE_SETS = [
    (EN_PROGRAMMING_TEMPLATES, "programming"),
    (EN_SCIENCE_TEMPLATES, "science"),
    (EN_TECHNICAL_TEMPLATES, "technical"),
    (EN_MATH_TEMPLATES, "mathematics"),
    (EN_DIALOGUE_TEMPLATES, "dialogue"),
    (EN_HISTORY_TEMPLATES, "history"),
]

# ============================================================
# Rich Russian content templates
# ============================================================

RU_PROGRAMMING_TEMPLATES = [
    "В Python {concept} используется для {action}. Например, вы можете определить {concept} с помощью ключевого слова '{keyword}'. Это позволяет разработчикам {benefit}. Вот как это работает: сначала вы объявляете {concept}, затем реализуете логику, и наконец вызываете его когда нужно. Паттерн {concept} фундаментален для написания чистого, поддерживаемого кода, который другие разработчики смогут легко понять и модифицировать.",
    "Понимание {concept} необходимо каждому программисту. Когда вы используете {concept}, вы можете {action} более эффективно. Ключевое преимущество заключается в том, что это обеспечивает {benefit}. Многие современные языки программирования поддерживают эту возможность, включая Python, JavaScript и C++. Давайте рассмотрим практический пример: представьте, что вам нужно обработать большой набор данных. Используя {concept}, вы можете выполнить эту задачу с минимальным количеством кода.",
    "Паттерн проектирования {concept} помогает разработчикам {action} структурированным образом. Этот паттерн особенно полезен, когда вам нужно {benefit}. В объектно-ориентированном программировании {concept} способствует повторному использованию кода и его поддерживаемости. Рассмотрим сценарий, где вы создаёте веб-приложение: реализация {concept} может значительно сократить дублирование кода и улучшить читаемость.",
    "При работе с {concept} важно понимать основополагающие принципы. Главная идея заключается в том, чтобы {action}, сохраняя при этом {benefit}. Этот подход широко используется в программной инженерии, потому что он упрощает сложные операции. Например, в приложении для работы с базами данных {concept} может помочь эффективно управлять соединениями, снижая риск утечки ресурсов.",
    "{concept} — одна из самых мощных возможностей современного программирования. Она позволяет вам {action} с лёгкостью. Основное преимущество — {benefit}, что делает ваш код более надёжным и масштабируемым. Профессиональные разработчики используют {concept} ежедневно для создания надёжных приложений. Изучение этого концепта значительно улучшит ваши навыки программирования.",
    "Типичный случай использования {concept} — когда вам нужно {action}. Реализация обычно включает создание {concept}, который обрабатывает основную логику. Следуя лучшим практикам, вы можете обеспечить {benefit} throughout вашей кодовой базы. Многие фреймворки предоставляют встроенную поддержку {concept}, упрощая интеграцию в существующие проекты.",
    "Эволюция {concept} в языках программирования былаremarkable. Ранние реализации были базовыми, но современные возможности {concept} предоставляют {benefit}, о которых десятилетия назад невозможно было мечтать. Сегодня разработчики могут {action} используя sofisticated инструменты и библиотеки. Понимание истории {concept} помогает appreciate, почему были приняты определённые проектные решения.",
    "Отладка проблем, связанных с {concept}, требует систематического подхода. Сначала определите, где используется {concept}. Затем проследите поток данных, чтобы понять, как выполняется {action}. Распространённые ошибки включают забытую обработку граничных случаев, что может compromiser {benefit}. Использование отладчика и добавление логов помогает точно определить источник проблемы.",
    "Оптимизация производительности часто включает улучшение реализации {concept}. Анализируя bottlenecks, разработчики могут {action} более эффективно. Техники включают кеширование результатов, сокращение ненужных вычислений и использование {benefit} для минимизации потребления ресурсов. Эти оптимизации могут привести к значительному ускорению, особенно в приложениях, обрабатывающих большие объёмы данных.",
    "Тестирование реализаций {concept} требует тщательного рассмотрения граничных случаев. Модульные тесты должны проверять, что {action} работает корректно в различных условиях. Интеграционные тесты гарантируют, что {concept} правильно взаимодействует с другими компонентами. Достижение {benefit} через комплексное тестирование даёт уверенность в предсказуемом поведении кода.",
]

RU_SCIENCE_TEMPLATES = [
    "Концепция {concept} в области {field} революционизировала наше понимание {topic}. Учёные обнаружили, что {concept} играет ключевую роль в {action}. Последние исследования показывают, что при правильном применении {concept} может привести к значительному {benefit}. Это открытие открыло новые направления для исследований в {field} и может в конечном итоге трансформировать наш подход к связанным задачам.",
    "В области {field} {concept} представляет собой фундаментальный принцип. Исследователи изучают {concept}, чтобы лучше понять, как работает {topic}. Последствия этого исследования обширны, влияя на всё от {action} до {benefit}. Понимание {concept} необходимо каждому, кто изучает {field}, так как оно формирует основу для более продвинутых тем и практических применений.",
    "Изучение {concept} было краеугольным камнем {field} на протяжении десятилетий. Благодаря тщательным наблюдениям и экспериментам учёные определили, что {concept} напрямую влияет на {topic}. Эта связь критически важна, потому что помогает объяснить {action}. Кроме того, практические применения {concept} продолжают расширяться, предлагая новые {benefit}, которые улучшают нашу повседневную жизнь.",
    "{concept} в {field} демонстрирует взаимосвязанность природных систем. Когда исследователи изучают {topic}, они обнаруживают, что {concept} является ключевым фактором в {action}. Это понимание привело к прорывным методам лечения и технологиям, которые обеспечивают {benefit}. Продолжающееся изучение {concept} обещает ещё больше открытий, которые могут изменить наше понимание природного мира.",
    "Современная {field} в значительной степени опирается на понимание {concept}. Анализируя {topic}, учёные могут предсказывать {action} с поразительной точностью. Эта предсказательная сила имеет множество применений, от улучшения {benefit} до разработки новых технологий. Изучение {concept} продолжает расширять границы человеческих знаний и вдохновляет новые поколения исследователей.",
    "Математические основы {concept} предоставляют строгую framework для понимания {topic}. Уравнения, описывающие {concept}, позволяют учёным моделировать {action} с точностью. Эти модели были подтверждены обширными экспериментами, подтверждая, что {benefit} может быть достигнуто через careful применение теоретических принципов. Взаимодействие между теорией и экспериментом驱动ит прогресс в {field}.",
    "Образовательные программы в {field} всё больше подчёркивают важность {concept}. Студенты изучают, как {concept} relates to {topic} через практические эксперименты и теоретические курсы. Этот dual подход гарантирует, что выпускники могут как понимать принципы behind {action}, так и применять их для достижения {benefit} в реальных ситуациях. Спрос на такую экспертизу продолжает расти.",
    "Международное сотрудничество ускорило исследования в области {concept}. Учёные из разных стран обмениваются данными о {topic}, позволяя проводить более масштабные исследования, чем любое отдельное учреждение могло бы провести. Этот кооперативный подход revealed, что {action} более сложен, чем previously thought, leading к refined теориям о {benefit}. Глобальный характер современной науки делает такое сотрудничество essential.",
    "Практические применения {concept} extend far beyond academic research. Индустрии от healthcare до technology rely on insights from {field} для {action}. Компании, которые понимают {concept}, могут разрабатывать продукты, предоставляющие {benefit} потребителям. Этот перевод научного знания в практические решения demonstrates реальную ценность фундаментальных исследований.",
    "Будущие направления исследований в {field} включают exploring новые аспекты {concept}. Учёные исследуют, как {topic} might be manipulated для {action} более эффективно. Ранние результаты suggest, что {benefit} could be significantly improved через novel подходы. Эти investigations требуют междисциплинарного сотрудничества, combining expertise из multiple fields для tackling complex questions.",
]

RU_TECHNICAL_TEMPLATES = [
    "Техническая документация для {concept}: Этот компонент разработан для {action} в рамках более крупной системы. Основной интерфейс предоставляет методы для {benefit}. Конфигурация выполняется через объект настроек, который принимает параметры для кастомизации. Обработка ошибок встроена, с соответствующими исключениями при обнаружении невалидных состояний. Пример использования: инициализируйте компонент, настройте параметры, затем вызовите основной метод для {action}.",
    "Справочник API: {concept} предоставляет чистый интерфейс для {action}. Основной класс предоставляет следующие методы: initialize() устанавливает внутреннее состояние, process() выполняет основную операцию {action}, и finalize() очищает ресурсы. Каждый метод возвращает объект статуса, указывающий на успех или ошибку. Модуль {concept} потокобезопасен и может использоваться в конкурентных средах для {benefit}.",
    "Обзор архитектуры: Система {concept} следует слоистой архитектуре. Слой представления обрабатывает взаимодействие с пользователем, слой бизнес-логики реализует {action}, а слой доступа к данным управляет сохранением. Это разделение ответственности гарантирует, что изменения в одном слое не влияют на другие. Система поддерживает {benefit} через настраиваемые плагины, расширяющие функциональность.",
    "Руководство по реализации: Для реализации {concept} следуйте этим шагам. Во-первых, определите интерфейс, который задаёт контракт для {action}. Во-вторых, создайте конкретную реализацию, выполняющую этот контракт. В-третьих, напишите модульные тесты для проверки корректности поведения. Наконец, интегрируйте реализацию в ваше приложение. Этот подход обеспечивает {benefit} и поддерживаемость на протяжении всего жизненного цикла разработки.",
    "Лучшие практики для {concept}: Всегда проверяйте входные данные перед {action}. Используйте соответствующую обработку ошибок для обнаружения и отчёта о проблемах. Документируйте ваш код тщательно, чтобы другие разработчики могли понять реализацию. Следуйте установленным соглашениям об именовании и стандартам кодирования. Тестируйте граничные случаи для обеспечения надёжности. Эти практики приводят к {benefit} в производственных средах.",
    "Considerations производительности: При развёртывании {concept} в production, monitor использование ресурсов carefully. Компонент должен {action} в acceptable latency thresholds. Если производительность degrades, consider optimizing реализацию или scaling horizontally. Стратегии кеширования могут предоставить {benefit}, reducing redundant computations. Load testing should be performed before deployment для identification potential bottlenecks.",
    "Guidelines безопасности: Компонент {concept} должен следовать best practices безопасности. Все inputs должны быть sanitized перед {action} для prevention injection attacks. Authentication и authorization checks должны быть performed на каждом layer. Sensitive data must be encrypted как in transit, так и at rest. Regular security audits help ensure {benefit} и protect against emerging threats.",
    "Руководство по миграции: При upgrade от previous версии {concept}, review changelog carefully. Breaking changes могут affect как вы {action}. Процесс миграции typically involves updating configuration files, modifying API calls, и running database migrations. Testing в staging environment перед production deployment ensures {benefit} и minimizes downtime during upgrade process.",
    "Troubleshooting: Common issues с {concept} включают configuration errors, resource exhaustion, и compatibility problems. Когда {action} fails, check logs для detailed error messages. Verify что все dependencies installed correctly и configuration parameters valid. Community forum предоставляет additional support, и documentation включает comprehensive FAQ section для {benefit}.",
    "Integration Patterns: {concept} can be integrated с various external systems. Most common pattern involves using {concept} для {action} while maintaining {benefit}. Adapter patterns help bridge differences between systems, while event-driven architectures enable loose coupling. Choosing right integration pattern depends on your specific requirements и constraints of existing infrastructure.",
]

RU_DIALOGUE_TEMPLATES = [
    "Пользователь: Можете объяснить, как работает {concept}? Ассистент: Конечно! {concept} — это фундаментальный концепт, который позволяет нам {action}. Представьте это как рецепт: у вас есть ингредиенты (входные данные), вы следуете шагам (обработка) и получаете блюдо (результат). Ключ в понимании того, как каждый шаг преобразует данные. Хотите, чтобы я разобрал конкретный пример? Пользователь: Да, пожалуйста! Ассистент: Отлично! Начнём с простого случая, где мы {action}. Сначала инициализируем переменные. Затем применяем {concept} для их преобразования. Результат — {benefit}. Понятно?",
    "Пользователь: Мне трудно понять {concept}. Ассистент: Не переживайте! Многие находят {concept} сложным на первых порах. Давайте разберём это проще. По своей сути {concept} — это про {action}. Представьте, что вы организуете библиотеку: вам нужна система для категоризации книг, быстрого поиска и поддержания порядка. {concept} делает именно это для данных. Пользователь: Эта аналогия помогает! Ассистент: Рад! Теперь посмотрим, как это применяется к {benefit} на практике.",
    "Пользователь: В чём разница между {concept} и {topic}? Ассистент: Отличный вопрос! Хотя оба относятся к {action}, они служат разным целям. {concept} фокусируется на структуре и организации, а {topic} — на поведении и взаимодействии. Думайте о {concept} как о чертеже, а о {topic} как о самом здании. Оба необходимы для {benefit}. Пользователь: То есть они дополняют друг друга? Ассистент: Именно! На самом деле, лучшие решения часто комбинируют оба подхода.",
    "Пользователь: Как мне реализовать {concept} в моём проекте? Ассистент: Хороший выбор! Вот пошаговый подход. Во-первых, определите, где {concept} вписывается в вашу архитектуру. Во-вторых, создайте необходимые структуры данных для поддержки {action}. В-третьих, реализуйте основную логику, обрабатывающую {benefit}. В-четвёртых, напишите тесты для проверки. Наконец, интегрируйте в основное приложение. Пользователь: Использовать библиотеку или писать с нуля? Ассистент: Зависит от ваших потребностей.",
    "Пользователь: Почему {concept} важен в современной разработке? Ассистент: {concept} стал необходимостью, потому что решает несколько ключевых задач. Во-первых, он улучшает {action}, предоставляя стандартизированный подход. Во-вторых, он усиливает {benefit} через лучшую организацию. В-третьих, он делает код более поддерживаемым, разделяя ответственность. В современном быстром темпе разработки эти преимущества бесценны. Пользователь: Есть ли минусы? Ассистент: Как любой инструмент, есть компромиссы.",
    "Пользователь: Можете привести реальный пример {concept}? Ассистент: Конечно! Рассмотрим социальную медиа платформу. Когда пользователи {action}, система использует {concept} для организации и отображения контента эффективно. Без {concept} платформа struggled бы с {topic}, leading к poor user experience. Implementing {concept} properly, платформа achieves {benefit}, keeping users engaged. Пользователь: Отличный пример! Ассистент: Рад предоставить больше примеров при необходимости.",
    "Пользователь: Какие распространённые ошибки при использовании {concept}? Ассистент: Хороший вопрос! Самая распространённая ошибка — misunderstanding когда нужно {action}. Некоторые разработчики overuse {concept}, adding unnecessary complexity. Другие underuse it, missing opportunities для {benefit}. Ключ — finding right balance. Start simple, then add {concept} где it provides clear value. Пользователь: Как узнать, когда правильное время? Ассистент: Look for patterns repetition или complexity.",
    "Пользователь: Как {concept} relates to {topic}? Ассистент: Они closely connected! {concept} provides mechanism для {action}, while {topic} defines context, в котором it operates. Think of {concept} как engine и {topic} как vehicle. Together, they enable {benefit}. Understanding this relationship helps you make better design decisions. Пользователь: That clarifies things a lot. Ассистент: Perfect! Let me know if you have more questions.",
    "Пользователь: Сложно ли изучить {concept}? Ассистент: Зависит от вашего background. Если вы familiar с {action}, you'll find {concept} intuitive. Core ideas straightforward, но mastering all details takes practice. Рекомендую starting с simple examples и gradually increasing complexity. С consistent effort, you'll achieve {benefit} в no time. Пользователь: Any recommended resources? Ассистент: There are excellent tutorials available online.",
    "Пользователь: Как тестировать мою реализацию {concept}? Ассистент: Testing {concept} involves several strategies. Unit tests verify что individual components {action} correctly. Integration tests ensure что {concept} works с other parts of system. Performance tests measure whether {benefit} meets your requirements. Рекомендую using testing framework, который supports all these types. Пользователь: What about edge cases? Ассистент: Absolutely! Edge case testing crucial for robustness.",
]

RU_CONCEPTS = ["функция", "класс", "переменная", "цикл", "массив", "словарь", "рекурсия", "наследование", "полиморфизм", "инкапсуляция", "абстракция", "интерфейс", "модуль", "пакет", "алгоритм", "структура данных", "база данных", "API", "фреймворк", "библиотека", "паттерн проектирования", "исключение", "поток", "процесс", "память", "кэш", "буфер", "очередь", "стек", "дерево", "граф", "хэш-таблица", "связный список", "бинарный поиск", "сортировка", "фильтрация", "маппинг", "редуцирование", "парсинг", "компиляция", "отладка", "тестирование", "развёртывание", "контроль версий", "непрерывная интеграция", "микросервис", "контейнер", "виртуализация", "сетевое взаимодействие", "протокол"]
RU_ACTIONS = ["обработка данных", "управление ресурсами", "организация информации", "выполнение операций", "преобразование входных данных", "проверка условий", "обработка ошибок", "оптимизация производительности", "хранение значений", "извлечение информации", "вычисление результатов", "фильтрация записей", "сортировка элементов", "объединение наборов данных", "разделение строк", "кодирование значений", "декодирование сообщений", "сжатие файлов", "шифрование данных", "аутентификация пользователей"]
RU_BENEFITS = ["улучшенная эффективность", "лучшая организация", "повышенная безопасность", "сниженная сложность", "повышенная надёжность", "более быстрое выполнение", "меньшее использование памяти", "более лёгкая поддержка", "лучшая масштабируемость", "улучшенная читаемость", "большая гибкость", "более сильная типизация", "чище архитектура", "быстрее разработка", "лучшее тестирование"]
RU_FIELDS = ["физика", "химия", "биология", "информатика", "математика", "инженерия", "психология", "социология", "экономика", "нейробиология"]
RU_TOPICS = ["природные явления", "сложные системы", "поведение человека", "технологический прогресс", "научное открытие", "математические взаимосвязи", "биологические процессы", "химические реакции", "физические законы", "вычислительные модели"]
RU_KEYWORDS = ["def", "class", "import", "from", "return", "yield", "async", "await", "try", "except", "for", "while", "if", "else", "lambda", "with", "raise", "assert", "pass", "break"]

RU_TEMPLATE_SETS = [
    (RU_PROGRAMMING_TEMPLATES, "programming"),
    (RU_SCIENCE_TEMPLATES, "science"),
    (RU_TECHNICAL_TEMPLATES, "technical"),
    (RU_DIALOGUE_TEMPLATES, "dialogue"),
]

# ============================================================
# Generation functions
# ============================================================

def generate_english(target=25000):
    all_data = []
    idx = 0
    generated = 0

    while len(all_data) < target:
        for templates, category in EN_TEMPLATE_SETS:
            if len(all_data) >= target:
                break
            template = random.choice(templates)
            text = template.format(
                concept=random.choice(EN_CONCEPTS),
                action=random.choice(EN_ACTIONS),
                benefit=random.choice(EN_BENEFITS),
                field=random.choice(EN_FIELDS),
                topic=random.choice(EN_TOPICS),
                keyword=random.choice(EN_KEYWORDS)
            )
            difficulty = random.choice(["beginner", "intermediate", "advanced"])
            all_data.append({
                "id": idx,
                "text": text,
                "category": category,
                "difficulty": difficulty
            })
            idx += 1
            generated += 1

            if generated % 1000 == 0:
                pct = int((len(all_data) / target) * 100)
                progress.update("en_gen", pct, f"generating", len(all_data))
                progress.render()

    return all_data[:target]

def generate_russian(target=25000):
    all_data = []
    idx = 0
    generated = 0

    while len(all_data) < target:
        for templates, category in RU_TEMPLATE_SETS:
            if len(all_data) >= target:
                break
            template = random.choice(templates)
            text = template.format(
                concept=random.choice(RU_CONCEPTS),
                action=random.choice(RU_ACTIONS),
                benefit=random.choice(RU_BENEFITS),
                field=random.choice(RU_FIELDS),
                topic=random.choice(RU_TOPICS),
                keyword=random.choice(RU_KEYWORDS)
            )
            difficulty = random.choice(["beginner", "intermediate", "advanced"])
            all_data.append({
                "id": idx,
                "text": text,
                "category": category,
                "difficulty": difficulty
            })
            idx += 1
            generated += 1

            if generated % 1000 == 0:
                pct = int((len(all_data) / target) * 100)
                progress.update("ru_gen", pct, f"generating", len(all_data))
                progress.render()

    return all_data[:target]

# ============================================================
# Main
# ============================================================

def main():
    os.system("")

    progress.register("en_gen", "Template Engine EN", "Local (60 templates)")
    progress.register("ru_gen", "Template Engine RU", "Local (40 templates)")

    render_thread = threading.Thread(target=render_loop, daemon=True)
    render_thread.start()

    print("Starting local data generation...\n")
    time.sleep(0.5)

    # Generate English
    progress.update("en_gen", 0, "starting", 0)
    progress.render()
    en_data = generate_english(target=25000)
    progress.complete("en_gen", len(en_data))
    progress.render()

    # Generate Russian
    progress.update("ru_gen", 0, "starting", 0)
    progress.render()
    ru_data = generate_russian(target=25000)
    progress.complete("ru_gen", len(ru_data))
    progress.render()

    # Save
    with open(DATA_DIR / "english_full.json", 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
    with open(DATA_DIR / "russian_full.json", 'w', encoding='utf-8') as f:
        json.dump(ru_data, f, ensure_ascii=False, indent=2)

    progress.stop()
    time.sleep(0.5)

    en_lines = sum(item['text'].count('\n') + 1 for item in en_data)
    ru_lines = sum(item['text'].count('\n') + 1 for item in ru_data)

    print("\n\n" + "=" * 70)
    print("  GENERATION COMPLETE")
    print("=" * 70)
    print(f"  English examples: {len(en_data)}  (~{en_lines} lines)")
    print(f"  Russian examples: {len(ru_data)}  (~{ru_lines} lines)")
    print(f"  Total: {len(en_data) + len(ru_data)} examples  (~{en_lines + ru_lines} lines)")
    print("=" * 70)

if __name__ == "__main__":
    main()
