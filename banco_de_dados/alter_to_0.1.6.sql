alter table telefonema drop constraint telefonema_id_conta_telefone_fk;
alter table telefonema add CONSTRAINT telefonema_id_conta_telefone_fk FOREIGN KEY(id_conta_telefone) REFERENCES conta_telefone (id) ON DELETE cascade;
