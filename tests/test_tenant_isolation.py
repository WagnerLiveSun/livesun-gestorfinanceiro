import unittest
from datetime import date

from src.app import create_app
from src.models import db, Empresa, User, Entidade, FluxoContaModel, ContaBanco, Lancamento


class TenantIsolationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app('testing')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.ctx = cls.app.app_context()
        cls.ctx.push()

        db.drop_all()
        db.create_all()

        empresa_a = Empresa(nome='Empresa A', cnpj='11111111000111')
        empresa_b = Empresa(nome='Empresa B', cnpj='22222222000122')
        db.session.add_all([empresa_a, empresa_b])
        db.session.flush()

        user_a = User(
            empresa_id=empresa_a.id,
            username='user_a',
            email='user_a@test.local',
            full_name='User A',
            is_active=True,
            is_admin=True,
        )
        user_a.set_password('123456')

        user_b = User(
            empresa_id=empresa_b.id,
            username='user_b',
            email='user_b@test.local',
            full_name='User B',
            is_active=True,
            is_admin=True,
        )
        user_b.set_password('123456')
        db.session.add_all([user_a, user_b])
        db.session.flush()

        fluxo_a = FluxoContaModel(empresa_id=empresa_a.id, codigo='1.1', descricao='Receita A', tipo='R', ativo=True)
        fluxo_b = FluxoContaModel(empresa_id=empresa_b.id, codigo='1.1', descricao='Receita B', tipo='R', ativo=True)
        db.session.add_all([fluxo_a, fluxo_b])
        db.session.flush()

        conta_a = ContaBanco(
            empresa_id=empresa_a.id,
            nome='Banco A',
            banco='A',
            agencia='0001',
            numero_conta='12345',
            ativo=True,
            saldo_inicial=1000,
            fluxo_conta_id=fluxo_a.id,
        )
        conta_b = ContaBanco(
            empresa_id=empresa_b.id,
            nome='Banco B',
            banco='B',
            agencia='0002',
            numero_conta='67890',
            ativo=True,
            saldo_inicial=2000,
            fluxo_conta_id=fluxo_b.id,
        )
        db.session.add_all([conta_a, conta_b])
        db.session.flush()

        entidade_a = Entidade(
            empresa_id=empresa_a.id,
            tipo='C',
            cnpj_cpf='00000000000001',
            nome='Cliente A',
            ativo=True,
        )
        entidade_b = Entidade(
            empresa_id=empresa_b.id,
            tipo='C',
            cnpj_cpf='00000000000002',
            nome='Cliente B',
            ativo=True,
        )
        db.session.add_all([entidade_a, entidade_b])
        db.session.flush()

        lancamento_a = Lancamento(
            empresa_id=empresa_a.id,
            data_evento=date(2026, 3, 1),
            data_vencimento=date(2026, 3, 2),
            data_pagamento=date(2026, 3, 2),
            status='pago',
            fluxo_conta_id=fluxo_a.id,
            conta_banco_id=conta_a.id,
            entidade_id=entidade_a.id,
            valor_real=100,
            valor_pago=100,
            numero_documento='DOC-A',
        )
        lancamento_b = Lancamento(
            empresa_id=empresa_b.id,
            data_evento=date(2026, 3, 1),
            data_vencimento=date(2026, 3, 2),
            data_pagamento=date(2026, 3, 2),
            status='pago',
            fluxo_conta_id=fluxo_b.id,
            conta_banco_id=conta_b.id,
            entidade_id=entidade_b.id,
            valor_real=250,
            valor_pago=250,
            numero_documento='DOC-B',
        )
        db.session.add_all([lancamento_a, lancamento_b])
        db.session.commit()

        cls.user_a_id = user_a.id
        cls.entidade_b_id = entidade_b.id
        cls.lancamento_b_id = lancamento_b.id

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.drop_all()
        cls.ctx.pop()

    def setUp(self):
        self.client = self.app.test_client()

    def _login_as_user_a(self):
        response = self.client.post(
            '/auth/login',
            data={'username': 'user_a', 'password': '123456'},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_entidades_list_isolated_by_company(self):
        self._login_as_user_a()

        response = self.client.get('/entidades/', follow_redirects=True)
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Cliente A', body)
        self.assertNotIn('Cliente B', body)

    def test_entidade_detail_blocks_cross_company_access(self):
        self._login_as_user_a()

        response = self.client.get(f'/entidades/{self.entidade_b_id}/ver')

        self.assertEqual(response.status_code, 404)

    def test_lancamento_edit_blocks_cross_company_access(self):
        self._login_as_user_a()

        response = self.client.get(f'/lancamentos/{self.lancamento_b_id}/editar')

        self.assertEqual(response.status_code, 404)

    def test_fluxo_csv_does_not_include_other_company_data(self):
        self._login_as_user_a()

        response = self.client.get('/relatorios/fluxo-caixa-csv')
        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('DOC-A', body)
        self.assertNotIn('DOC-B', body)


if __name__ == '__main__':
    unittest.main()
