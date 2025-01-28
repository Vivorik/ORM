from peewee import *
import datetime

db = SqliteDatabase('DatNew1.db') 

class Client(Model):
    name = CharField()
    phone = CharField()

    class Meta:
        database = db

class Employee(Model):
    name = CharField()
    phone = CharField()
    position = CharField()

    class Meta:
        database = db
        
class Project(Model):
    name = CharField()
    adress = CharField()
    id_employee = ForeignKeyField(Employee, backref='posts')
    deadline = DateField()
    id_client = ForeignKeyField(Client, backref='posts')
    status = CharField(
        constraints=[Check("status IN ('Planned', 'In Progress', 'Completed')")],
        null=False,
        default='Planned'
    )

    class Meta:
        database = db        

class Project_Check(Model):
    id_project = ForeignKeyField(Project, backref='posts')
    description = CharField()
    summ = IntegerField()
    date_check = DateField()
    phone = CharField()

    class Meta:
        database = db

class Supplier(Model):
    name = CharField()
    adress = CharField()
    phone = CharField()

    class Meta:
        database = db

class Material(Model):
    id_supplier = ForeignKeyField(Supplier, backref='posts')
    name = CharField()
    summ = IntegerField()

    class Meta:
        database = db

class Additional(Model):
    summ = IntegerField()
    description = CharField()

    class Meta:
        database = db
        
class Expense(Model):
    expense_date = DateField()
    id_project = ForeignKeyField(Project, backref='posts')
    id_additional = ForeignKeyField(Additional, backref='posts')

    class Meta:
        database = db
        
class Expense_Material(Model):
    id_expense = ForeignKeyField(Expense, backref='posts')
    id_material = ForeignKeyField(Material, backref='posts')
    quantity = IntegerField()

    class Meta:
        database = db
        
class Administrator(Model):
    Login = CharField()
    Password = CharField()

    class Meta:
        database = db
        
db.connect()
db.create_tables([Client, Employee, Project, Project_Check, Supplier, Material, Additional, Expense, Expense_Material, Administrator])
#Возвращает годовую прибыль(разность между годовым доходом и годовым расходом) (Используется для составления отчетов и статистики, а также для просчета стратегии на следующие года)
today = datetime.date.today()
current_year = datetime.date.today().year

query_additional = (
    Additional.select(fn.SUM(Additional.summ).alias('total')).join(Expense, on=(Expense.id_additional == Additional.id)).where(fn.strftime('%Y', Expense.expense_date) == str(current_year))
)

query_expense_material = (
    Expense_Material.select(fn.SUM(Expense_Material.quantity * Material.summ).alias('total')).join(Material, on=(Material.id == Expense_Material.id_material)).join(Expense, on=(Expense.id == Expense_Material.id_expense)).where(fn.strftime('%Y', Expense.expense_date) == str(current_year))
)


project_check_sum = (
    Project_Check.select(fn.SUM(Project_Check.summ).alias('total')).where(fn.strftime('%Y', Project_Check.date_check) == str(current_year))
)

query_expense_material_total = query_expense_material.scalar() or 0
query_additional_total = query_additional.scalar() or 0
project_check_sum_total = project_check_sum.scalar() or 0

query1 = project_check_sum_total - (query_expense_material_total + query_additional_total)
print(f"Result of year: {query1}")

print(f"-----------------")
#Возвращает подсчет количества проектов по статусам (Важно для определения нынешних задач, составления статистики)
query2 = (
    Project.select(Project.status, fn.COUNT(Project.id)).group_by(Project.status).order_by(fn.COUNT(Project.id).desc())
)
print("Projects count by status:")
for row in query2.tuples():
    status, count = row
    print(f"Status: {status}, Count: {count}")
print(f"-----------------")
#Возвращает клиента, количество его заказов и общую стоимость (Может использоваться для определения частых клиентов и возможного последующего предоставления скидок или специальных предложений)
query3 = (
    Client.select(
        Client.name,
        fn.COUNT(Project.id).alias('project_count'),
        fn.SUM(Project_Check.summ).alias('total_sum')
    ).join(Project, on=(Project.id_client == Client.id)).join(Project_Check, on=(Project_Check.id_project == Project.id)).group_by(Client.name)
)

print("Client info:")
for row in query3:
    print(f"Name: {row.name}, Count of project: {row.project_count}, Total sum: {row.total_sum}")
print(f"-----------------")
#Возвращает самые популярные проекты (Может быть полезно при создании рекламы)
query4 = (
    Project.select(
        Project.name,
        fn.COUNT(Project_Check.id).alias('quantity')
    ).join(Project_Check, on=(Project_Check.id_project == Project.id)).group_by(Project.name).order_by(fn.COUNT(Project_Check.id).desc())
)

print("Project info:")
for row in query4:
    print(f"Name: {row.name}, Quantity: {row.quantity}")
print(f"-----------------")
#Возвращает самые часто используемые материалы (Используется при закупках и составлении статистики о поставщиках)
query5 = (
    Material.select(
        Material.name,
        fn.SUM(Expense_Material.quantity).alias('quantity')
    ).join(Expense_Material, on=(Expense_Material.id_material == Material.id)).group_by(Material.id).having(fn.SUM(Expense_Material.quantity) > 100).order_by(fn.SUM(Expense_Material.quantity).desc())
)

print("Material info:")
for row in query5:
    print(f"Name: {row.name}, Quantity: {row.quantity}")
print(f"-----------------")
#Возвращает информацию о 3 проектах с минимальным бюджетом (Имеет смысл для осмысления наиболее выгодных проектов)
query6 = (
    Project.select(
        Project.name,
        Project.adress,
        Project.status,
        Project_Check.summ
    ).join(Project_Check, on=(Project_Check.id_project == Project.id)).order_by(Project_Check.summ.asc()).limit(3)
)

print("Project info:")
for row in query6.tuples():
    name, adress, status, summ = row
    print(f"Name: {name}, Address: {adress}, Status: {status}, Sum: {summ}")
print(f"-----------------")
#Возвращает ответственного сотрудника за каждый проект (Используется для определения ответственного лица за каждый проект или для нахождения наименее(наиболее) занятых сотрудников)
query7 = (
    Employee.select(
        Employee.name,
        Project.name
    ).join(Project, on=(Project.id_employee == Employee.id))
)

print("Project responsible employee:")
for row in query7.tuples():
    employee_name, project_name = row
    print(f"Employee name: {employee_name}, Project name: {project_name}")
print(f"-----------------")
#Возвращает все проекты, которые необходимо закончить в этом месяце (Используется для определения наиболее важных текущих задач)
query8 = (
    Project.select(
        Project.name,
        Project.adress,
        Employee.name,
        Project.deadline,
        Client.name,
        Project.status
    ).join(Client, on=(Client.id == Project.id_client)).join(Employee, on=(Employee.id == Project.id_employee)).where(
        ((Project.status == 'In Progress') | (Project.status == 'Planned')) &
        (fn.strftime('%m', Project.deadline) == fn.strftime('%m', datetime.date.today())) &
        (fn.strftime('%Y', Project.deadline) == fn.strftime('%Y', datetime.date.today()))
    )
)

print("Project info:")
for row in query8.tuples():
    project_name, adress, employee_name, deadline, client_name, status = row
    print(f"Name: {project_name}, Address: {adress}, Employee name: {employee_name}, Deadline: {deadline}, Client name: {client_name}, Status: {status}")
print(f"-----------------")
#Возвращает все материалы, используемые в проекте (Используется для составления отчета)
query9 = (
    Material.select(
        Project.name,
        Material.name,
        Expense_Material.quantity
    ).join(Expense_Material, on=(Expense_Material.id_material == Material.id)).join(Expense, on=(Expense.id == Expense_Material.id_expense)).join(Project, on=(Project.id == Expense.id_project))
)

print("Material usage info:")
for row in query9.tuples():
    project_name, material_name, quantity = row
    print(f"Project name: {project_name}, Material name: {material_name}, Quantity: {quantity}")
print(f"-----------------")
#Возвращает название материалов и их поставщиков (Используется для поиска поставщика каждого материала)
query10 = (
    Material.select(
        Material.name,
        Supplier.name
    ).join(Supplier, on=(Material.id_supplier == Supplier.id)).group_by(Supplier.name)
)

print("Material and supplier info:")
for row in query10.tuples():
    material_name, supplier_name = row
    print(f"Material name: {material_name}, Supplier name: {supplier_name}")


db.close()
