# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import logging
import formencode

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect
from pylons.decorators.rest import restrict, dispatch_on
from republicaos.lib.helpers import get_object_or_404, url, flash
from republicaos.lib.utils import render, validate, extract_attributes
from republicaos.lib.base import BaseController
from republicaos.model import Pessoa, CadastroPendente, TrocaSenha, ConviteMorador, Session
from republicaos.model import Morador
from republicaos.lib.validators import Unique, Captcha
from formencode import Schema, validators
from republicaos.lib.auth import owner_required
from sqlalchemy.sql.expression import desc
from republicaos.lib.captcha import captcha


log = logging.getLogger(__name__)


class PessoaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True, strip=True)
    email = formencode.All(validators.Email(not_empty=True), Unique(model=Pessoa, attr='email'))
    senha = validators.UnicodeString(not_empty=True, min=4)
    confirmacao_senha = validators.UnicodeString()
    captcha = Captcha(resposta='captcha_md5', not_empty=True)
    aceito_termos = validators.NotEmpty(messages={'empty': 'Aceite os termos de uso'})
    chained_validators = [validators.FieldsMatch('senha', 'confirmacao_senha')]


class PessoaEdicaoSchema(Schema):
    '''
    A senha não é obrigatória nesse caso, a não ser que queira mudá-la
    '''
    allow_extra_fields = True
    filter_extra_fields = True
    nome = validators.UnicodeString(not_empty=True, strip=True)
    email = validators.Email(not_empty=True)
    senha = validators.UnicodeString()
    confirmacao_senha = validators.UnicodeString()
    chained_validators = [validators.FieldsMatch('senha', 'confirmacao_senha')]


class TrocaSenhaSchema(Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    email = validators.Email(not_empty=True)


class PessoaController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""

    def __before__(self, id=None):
        if id:
            c.pessoa = get_object_or_404(Pessoa, id = id)

    @dispatch_on(GET='list', POST='create')
    def rest_dispatcher_collection(self):
        abort(406)

    @dispatch_on(GET='retrieve', PUT='update', DELETE='delete')
    def rest_dispatcher_single(self, id):
        abort(406)

    # Métodos REST. A idéia é que não usem interface alguma. Equivalem a get/set de objetos
    # CRUD - Create | Retrieve | Update | Delete

    @restrict("GET")
    def list(self):
        pass

    @restrict("POST")
    @validate(PessoaSchema) # pra garantir
    def create(self):
        """POST /pessoa: Create a new item"""
        if not c.valid_data:
            abort(406)
        c.pessoa = Pessoa(**c.valid_data)
        Session.commit()
        # TODO: precisa retornar código 201 - Created
        response.status = 201 # Created
        return

    @restrict("GET")
    def retrieve(self, id):
        return c.pessoa.to_dict()

    @restrict("PUT")
    @validate(PessoaSchema) # pra garantir
    def update(self, id):
        """PUT /pessoa/id: Update an existing item"""
        if not c.valid_data:
           abort(406)
        c.pessoa.from_dict(c.valid_data)
        Session.commit()
        return

    @restrict("DELETE")
    def delete(self, id):
        """DELETE /pessoa/id: Delete an existing item"""
        abort(403)
        # se fosse permitido apagar, deveria retornar status 200 OK

    # Demais métodos relacionados à formulários

    def index(self):
        """GET /pessoa: All items in the collection"""
        c.pessoas = Pessoa.query.order_by(Pessoa.nome).all()
        return render('pessoa/index.html')


    @validate(PessoaSchema)
    def new(self):
        """GET /pessoa/new: Form to create a new item"""
        if c.valid_data:
            pendencia = CadastroPendente.get_by(email = c.valid_data['email'])
            if not pendencia:
                pendencia = CadastroPendente(**c.valid_data)
            else:
                pendencia.from_dict(c.valid_data)
                flash('(info) Já existe um pedido de cadastro pendente para o e-mail fornecido.')
            Session.commit()
            redirect(controller='root', action='index')
        c.action = url(controller='pessoa', action='new')
        c.submit = 'Criar'
        c.title  = 'Crie sua conta'
        c.voltar_para = url(controller='root', action='index')
        c.captcha, c.captcha_md5 = captcha()
        return render('pessoa/form.html', filler_data=request.params)



    @owner_required
    @validate(PessoaEdicaoSchema)
    def edit(self, id, format='html'):
        """GET /pessoa/edit/id: Edit a specific item"""
        c.voltar_para = url(controller='pessoa', action='painel', id=id)
        if c.valid_data:
            if not c.valid_data['senha']: # alteração de senha não é obrigatória na edição
                c.valid_data.pop('senha')
            request.method = 'PUT'
            self.update(id)
            flash('(info) Dados alterados com sucesso!')
            # algum outro processamento para determinar a localização da república e agregar
            # serviços próximos
            redirect(c.voltar_para)
        elif not c.errors:
            filler_data = c.pessoa.to_dict()
        else:
            log.debug('PessoaController.edit: c.errors: %r' % c.errors)
            filler_data = request.params
        c.action = url(controller='pessoa', action='edit', id=id)
        c.submit = 'Atualizar'
        c.title = 'Editar Dados Pessoais'
        return render('pessoa/form.html', filler_data = filler_data)


    def show(self, id):
        """GET /pessoa/show/id: Show a specific item"""
        c.title = 'Pessoa'
        return render('pessoa/form.html', filler_data = c.pessoa.to_dict())
    
    
    @validate(TrocaSenhaSchema)
    def esqueceu_senha(self):
        if c.valid_data:
            pessoa = Pessoa.get_by(email = c.valid_data['email'])
            if pessoa:
                TrocaSenha(pessoa=pessoa)
                Session.commit()
                redirect(controller='root', action='index')
            else:
                flash('(error) Este endereço de e-mail não está cadastrado no Republicaos!')
        
        return render('pessoa/esqueceu_senha.html')
    
    @owner_required
    def painel(self, id):
        c.title = 'Painel de Controle'
        c.registros = Morador.query.filter(Morador.pessoa_id == c.user.id).order_by(desc(Morador.entrada)).all()
        c.can_create = len(c.user.morador_em_republicas) < 2
        c.convites = ConviteMorador.query.filter(ConviteMorador.email == c.user.email).all()
        return render('pessoa/painel.html')
        