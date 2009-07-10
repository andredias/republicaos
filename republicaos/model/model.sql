CREATE TABLE aluguel (
	data_cadastro DATE NOT NULL, 
	republica_id INTEGER NOT NULL, 
	valor NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (data_cadastro, republica_id), 
	 CONSTRAINT aluguel_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id)
);
CREATE TABLE conta_telefone (
	id INTEGER NOT NULL, 
	vencimento DATE NOT NULL, 
	emissao DATE NOT NULL, 
	telefone NUMERIC(12, 0) NOT NULL, 
	operadora_id INTEGER NOT NULL, 
	franquia NUMERIC(10, 2), 
	servicos NUMERIC(10, 2), 
	republica_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT conta_telefone_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id), 
	 UNIQUE (telefone, emissao)
);
CREATE TABLE despesa (
	id INTEGER NOT NULL, 
	data DATE NOT NULL, 
	quantia NUMERIC(10, 2) NOT NULL, 
	responsavel_id INTEGER NOT NULL, 
	tipo_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT despesa_responsavel_id_fk FOREIGN KEY(responsavel_id) REFERENCES morador (id), 
	 CONSTRAINT despesa_tipo_id_fk FOREIGN KEY(tipo_id) REFERENCES tipo_despesa (id)
);
CREATE TABLE despesa_periodica (
	id INTEGER NOT NULL, 
	proximo_vencimento DATE NOT NULL, 
	quantia NUMERIC(10, 2) NOT NULL, 
	data_termino DATE, 
	responsavel_id INTEGER NOT NULL, 
	tipo_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT despesa_periodica_responsavel_id_fk FOREIGN KEY(responsavel_id) REFERENCES morador (id), 
	 CONSTRAINT despesa_periodica_tipo_id_fk FOREIGN KEY(tipo_id) REFERENCES tipo_despesa (id)
);
CREATE TABLE fechamento (
	data DATE NOT NULL, 
	republica_id INTEGER NOT NULL, 
	PRIMARY KEY (data, republica_id), 
	 CONSTRAINT fechamento_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id)
);
CREATE TABLE morador (
	id INTEGER NOT NULL, 
	data_entrada DATE NOT NULL, 
	data_saida DATE, 
	republica_id INTEGER NOT NULL, 
	pessoa_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT morador_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id), 
	 UNIQUE (pessoa_id, republica_id), 
	 CONSTRAINT morador_pessoa_id_fk FOREIGN KEY(pessoa_id) REFERENCES pessoa (id)
);
CREATE TABLE peso_quota (
	data_cadastro DATE NOT NULL, 
	morador_id INTEGER NOT NULL, 
	peso_quota NUMERIC(10, 2) NOT NULL, 
	PRIMARY KEY (data_cadastro, morador_id), 
	 CONSTRAINT peso_quota_morador_id_fk FOREIGN KEY(morador_id) REFERENCES morador (id)
);
CREATE TABLE pessoa (
	id INTEGER NOT NULL, 
	nome VARCHAR(30), 
	senha VARCHAR(40), 
	e_mail VARCHAR(255), 
	contato VARCHAR, 
	criacao TIMESTAMP, 
	PRIMARY KEY (id), 
	 UNIQUE (nome), 
	 UNIQUE (e_mail)
);
CREATE TABLE republica (
	id INTEGER NOT NULL, 
	nome VARCHAR(90) NOT NULL, 
	data_criacao DATE NOT NULL, 
	logradouro VARCHAR(150), 
	complemento VARCHAR(100), 
	cidade VARCHAR(80), 
	uf VARCHAR(2), 
	cep VARCHAR(8), 
	PRIMARY KEY (id)
);
CREATE TABLE telefone (
	numero NUMERIC(12, 0) NOT NULL, 
	republica_id INTEGER NOT NULL, 
	descricao VARCHAR, 
	responsavel_id INTEGER NOT NULL, 
	PRIMARY KEY (numero, republica_id), 
	 CONSTRAINT telefone_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id), 
	 CONSTRAINT telefone_responsavel_id_fk FOREIGN KEY(responsavel_id) REFERENCES morador (id)
);
CREATE TABLE telefonema (
	numero NUMERIC(12, 0) NOT NULL, 
	conta_telefone_id INTEGER NOT NULL, 
	tipo_fone INTEGER NOT NULL, 
	tipo_distancia INTEGER NOT NULL, 
	segundos INTEGER NOT NULL, 
	quantia NUMERIC(10, 2) NOT NULL, 
	responsavel_id INTEGER, 
	PRIMARY KEY (numero, conta_telefone_id), 
	 CONSTRAINT telefonema_conta_telefone_id_fk FOREIGN KEY(conta_telefone_id) REFERENCES conta_telefone (id) ON DELETE cascade, 
	 CONSTRAINT telefonema_responsavel_id_fk FOREIGN KEY(responsavel_id) REFERENCES morador (id)
);
CREATE TABLE tipo_despesa (
	id INTEGER NOT NULL, 
	nome VARCHAR(40) NOT NULL, 
	descricao VARCHAR, 
	republica_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	 CONSTRAINT tipo_despesa_republica_id_fk FOREIGN KEY(republica_id) REFERENCES republica (id)
);
CREATE INDEX ix_aluguel_republica_id ON aluguel (republica_id);
CREATE INDEX ix_conta_telefone_republica_id ON conta_telefone (republica_id);
CREATE INDEX ix_despesa_periodica_responsavel_id ON despesa_periodica (responsavel_id);
CREATE INDEX ix_despesa_periodica_tipo_id ON despesa_periodica (tipo_id);
CREATE INDEX ix_despesa_responsavel_id ON despesa (responsavel_id);
CREATE INDEX ix_despesa_tipo_id ON despesa (tipo_id);
CREATE INDEX ix_fechamento_republica_id ON fechamento (republica_id);
CREATE INDEX ix_morador_pessoa_id ON morador (pessoa_id);
CREATE INDEX ix_morador_republica_id ON morador (republica_id);
CREATE INDEX ix_peso_quota_morador_id ON peso_quota (morador_id);
CREATE INDEX ix_telefone_republica_id ON telefone (republica_id);
CREATE INDEX ix_telefone_responsavel_id ON telefone (responsavel_id);
CREATE INDEX ix_telefonema_conta_telefone_id ON telefonema (conta_telefone_id);
CREATE INDEX ix_telefonema_responsavel_id ON telefonema (responsavel_id);
CREATE INDEX ix_tipo_despesa_republica_id ON tipo_despesa (republica_id);
