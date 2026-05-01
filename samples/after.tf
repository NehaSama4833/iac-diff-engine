# samples/after.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/8"  # changed — wider CIDR
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # opened SSH to internet — HIGH risk
  }
}

resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.large"  # changed instance type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
}

resource "aws_db_instance" "main" {  # new resource
  identifier        = "prod-db"
  engine            = "postgres"
  instance_class    = "db.t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]
}