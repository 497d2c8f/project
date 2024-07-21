from module import *




# добавить константы для каждого режима работы




#pprint(get_filepaths('*', directory='/home', full_path=True))
#sys.exit(1)




if not os.path.isdir(VOTINGS_WD):
	os.mkdir(VOTINGS_WD)




print('''
###########
Голосование
###########
''')




main_password = get_h_file_key()
keypairs = get_keypairs(main_password)




print('\nРежимы работы:\n\n0. Выход\n1. Голосующий\n2. Посредник\n3. Агенство\n4. Создать новые ключи')
option_1 = input('\nВыберите режим работы и нажмите Enter: ')

								# добавить возможность чтения файла с результатами голосования и проверки этих результатов, подписи и т.д.


if option_1 == '0':

	sys.exit(1)




if option_1 == '1':

	e_sign_pk = keypairs['sign_pk']
	e_sign_sk = keypairs['sign_sk']
	e_kem_pk = keypairs['kem_pk']
	e_kem_sk = keypairs['kem_sk']

	option_2 = input('\n0. Выход\n1. Первый этап\n2. Второй этап\n\nВыберите и нажмите Enter: ')

	if option_2 == '0':

		sys.exit(1)

	if option_2 == '1':

		e = {}
		voting_file_path = input('\nПеретащите сюда файл голосования "voting__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		e['v'] = read_file(voting_file_path)['voting']
		v_keys = e['v'].get_keys()
		e['m_sign_pk'] = list(v_keys['d_sel_m_pk'].keys())[0]
		e['m_kem_pk'] = list(v_keys['d_sel_m_pk'].values())[0]
		e['a_sign_pk'] = v_keys['a_sign_pk']
		e['a_kem_pk'] = v_keys['a_kem_pk']
		e['s_a_lvp'] = e['v'].get_s_a_lvp()
		e['k_em'] = get_random_bytes(32)
		e['k_ea'] = get_random_bytes(32)
		print('\nОзнакомьтесь с голосованием.')
		e['v'].pretty_print()
		choice = int(input('\nВведите выбранный номер ответа: '))
		e['b'] = Ballot(e['v'].get_v_id(), choice)
		st1_e_data = st1_e(
			e['v'],
			e['b'],
			e['k_em'],
			e['k_ea'],
			e_sign_pk,
			e_sign_sk
		)
		e = {**e, **st1_e_data}
		write_file(os.path.join(VOTINGS_WD, e['v'].get_v_id()[0:8].hex(), f'e_data__{e["v"].get_v_id()[0:8].hex()}_{e_sign_pk[0:8].hex()}.bin'), main_password, **e)
		write_file(os.path.join(VOTINGS_WD, e['v'].get_v_id()[0:8].hex(), f'msg1_em__{e["v"].get_v_id()[0:8].hex()}_{e_sign_pk[0:8].hex()}_{e["m_sign_pk"][0:8].hex()}.bin'), msg1_em=e['msg1_em'])

		print('\nПервый этап успешно пройден.')

	if option_2 == '2':
		voting_dirname = get_voting_dirname()
		voting_dirpath = os.path.join(VOTINGS_WD, voting_dirname)
		e_data_file_path = get_filepaths(f'e_data__{voting_dirname}_*.bin', directory=voting_dirpath, full_path=True)[0]
		e = read_file(e_data_file_path, main_password)
		s_m_l_h_e_eaek_b_file_path = input('\nПеретащите сюда файл "s_m_l_h_e_eaek_b__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		e['s_m_l_h_e_eaek_b'] = read_file(s_m_l_h_e_eaek_b_file_path)['s_m_l_h_e_eaek_b']
	
		st3_e_data = st3_e(e['s_m_l_h_e_eaek_b'], e['v'], e['e_eaek_b'], e_sign_pk, e_sign_sk, e['k_em'])
		e = {**e, **st3_e_data}

		write_file(e_data_file_path, main_password, **e)
		write_file(os.path.join(VOTINGS_WD, e['v'].get_v_id()[0:8].hex(), f'msg3_em__{e["v"].get_v_id()[0:8].hex()}_{e_sign_pk[0:8].hex()}_{e["m_sign_pk"][0:8].hex()}.bin'), msg3_em=e['msg3_em'])
#		delete_paths('msg1_em__*.bin')

		print('\nВторой этап успешно пройден.')




if option_1 == '2':

	m_sign_pk = keypairs['sign_pk']
	m_sign_sk = keypairs['sign_sk']
	m_kem_pk = keypairs['kem_pk']
	m_kem_sk = keypairs['kem_sk']

	option_2 = input('\n0. Выход\n1. Первый этап\n2. Второй этап\n\nВыберите и нажмите Enter: ')

	if option_2 == '0':

		sys.exit(1)

	if option_2 == '1':

		m = {}
		voting_file_path = input('\nПеретащите сюда голосования "voting__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		m['v'] = read_file(voting_file_path)['voting']
		m['a_sign_pk'] = m['v'].get_keys()['a_sign_pk']
		m['a_kem_pk'] = m['v'].get_keys()['a_kem_pk']
		m['s_a_lvp'] = m['v'].get_s_a_lvp()
		msg1_em_files_dir = input('\nПеретащите сюда папку с файлами "msg1_em__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		msg1_em_filepaths = get_filepaths(f'msg1_em__{m["v"].get_v_id()[0:8].hex()}_*.bin', directory=msg1_em_files_dir, full_path=True)
		l_msg1_em = []
		for path in msg1_em_filepaths:
			try:
				l_msg1_em.append(read_file(path)['msg1_em'])
			except:
				pass

		st2_m_data = st2_m(m['s_a_lvp'], l_msg1_em, m['v'].get_v_id(), m_sign_pk, m_sign_sk, m_kem_sk, m['a_sign_pk'])
		m = {**m, **st2_m_data}

		write_file(os.path.join(VOTINGS_WD, m['v'].get_v_id()[0:8].hex(), f'm_data__{m["v"].get_v_id()[0:8].hex()}_{m_sign_pk[0:8].hex()}.bin'), main_password, **m)
		write_file(os.path.join(VOTINGS_WD, m['v'].get_v_id()[0:8].hex(), f's_m_l_h_e_eaek_b__{m["v"].get_v_id()[0:8].hex()}_{m_sign_pk[0:8].hex()}.bin'), s_m_l_h_e_eaek_b=m['s_m_l_h_e_eaek_b'])

		print('\nПервый этап успешно пройден.')

	if option_2 == '2':

		voting_dirname = get_voting_dirname()
		voting_dirpath = os.path.join(VOTINGS_WD, voting_dirname)
		m_data_file_path = get_filepaths(f'm_data__{voting_dirname}_*.bin', directory=voting_dirpath, full_path=True)[0]
		m = read_file(m_data_file_path, main_password)
		msg3_em_files_dir = input('\nПеретащите сюда папку с файлами "msg3_em__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		msg3_em_filepaths = get_filepaths(f'msg3_em__{m["v"].get_v_id()[0:8].hex()}_*.bin', directory=msg3_em_files_dir, full_path=True)
		l_msg3_em = []
		for path in msg3_em_filepaths:
			try:
				l_msg3_em.append(read_file(path)['msg3_em'])
			except:
				pass
		m['l_msg3_em'] = l_msg3_em

		st4_m_data = st4_m(
			m['l_msg3_em'],
			m['v'].get_v_id(),
			m_sign_pk,
			m_sign_sk,
			m['a_sign_pk'],
			m['a_kem_pk'],
			m['d_msg1_em']
		)
		m = {**m, **st4_m_data}

		write_file(m_data_file_path, main_password, **m)
		write_file(os.path.join(VOTINGS_WD, voting_dirname, f's_m_msg4_ma__{m["v"].get_v_id()[0:8].hex()}_{m_sign_pk[0:8].hex()}_{m["a_sign_pk"][0:8].hex()}.bin'), s_m_msg4_ma=m['s_m_msg4_ma'])    #тут можно заменить v_id на voting_dirname
#		delete_paths('s_m_l_h_e_eaek_b__*.bin')

		print('\nВторой этап успешно пройден.')




if option_1 == '3':

	a_sign_pk = keypairs['sign_pk']
	a_sign_sk = keypairs['sign_sk']
	a_kem_pk = keypairs['kem_pk']
	a_kem_sk = keypairs['kem_sk']

	option_2 = input('\n0. Выход\n1. Создать файл голосования\n2. Обработать финальный этап протокола\n\nВыберите и нажмите Enter: ')

	if option_2 == '0':

		sys.exit(1)

	if option_2 == '1':

		l_vp_sign_pk = []
		if input('\nВ голосовании может участвовать любой желающий?\n\n1. Да\n2. Нет\n\nВыберите и нажмите Enter: ') == '2':
			keys_public_files_dir = input('\nПеретащите сюда папку с открытыми ключами участников голосования, допущенных до голосования, и нажмите Enter: ').replace('\'', '').rstrip(' ')
			keys_public_filepaths = get_filepaths('keys_public__*.bin', directory=keys_public_files_dir, full_path=True)
			for path in keys_public_filepaths:
				try:
					l_vp_sign_pk.append(read_file(path)['sign_pk'])
				except:
					pass
		question = input('\nВведите вопрос и нажмите Enter: ')
		description = input('\nВведите описание и нажмите Enter: ')
		options = []
		options_number = int(input('\nВведите количество вариантов ответа и нажмите Enter: '))
		while options_number:
			options.append(input('\nВведите вариант ответа и нажмите Enter: '))
			options_number -= 1
		v = Voting(a_sign_pk, a_kem_pk, question, description, options)
		s_a_lvp = Sign(LVP(l_vp_sign_pk, v.get_v_id()), a_sign_pk, a_sign_sk)
		v.set_s_a_lvp(s_a_lvp)
		write_file(os.path.join(VOTINGS_WD, v.get_v_id()[0:8].hex(), f'voting__{v.get_v_id()[0:8].hex()}.bin'), voting=v)

		print(f'\nФайл голосования "voting__{v.get_v_id()[0:8].hex()}.bin" успешно создан. Он находится в папке "votings".')

	if option_2 == '2':

		a = {}
		voting_file_path = input('\nПеретащите сюда скачанный уже с сайта файл "voting__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		a['v'] = read_file(voting_file_path)['voting']
		s_m_msg4_ma_files_dir = input('\nПеретащите сюда папку с файлами "s_m_msg4_ma__*.bin" и нажмите Enter: ').replace('\'', '').rstrip(' ')
		s_m_msg4_ma_filepaths = get_filepaths(f's_m_msg4_ma__{a["v"].get_v_id()[0:8].hex()}_*.bin', directory=s_m_msg4_ma_files_dir, full_path=True)
		l_s_m_msg4_ma = []
		for path in s_m_msg4_ma_filepaths:
			try:
				l_s_m_msg4_ma.append(read_file(path)['s_m_msg4_ma'])
			except:
				pass
		a['l_s_m_msg4_ma'] = l_s_m_msg4_ma

		st5_a_data = st5_a(
			a['v'],
			a['l_s_m_msg4_ma'],
			a_sign_pk,
			a_sign_sk,
			a_kem_pk,
			a_kem_sk
		)
		a = {**a, **st5_a_data}
		write_file(os.path.join(VOTINGS_WD, a['v'].get_v_id()[0:8].hex(), f'a_data__{a["v"].get_v_id()[0:8].hex()}_{a_sign_pk[0:8].hex()}.bin'), main_password, **a)
		write_file(os.path.join(VOTINGS_WD, a['v'].get_v_id()[0:8].hex(), f's_a_vres__{a["v"].get_v_id()[0:8].hex()}_{a_sign_pk[0:8].hex()}.bin'), s_a_vres=a['s_a_vres'])
#			delete_paths('s_m_msg4_ma__*.bin')
		options = a['v'].get_data()['options']
		vres = {option: 0 for option in options}
		for m_sign_pk, l_rfp, l_b in a['s_a_vres'].get_data():
			for b in l_b:
				choice = b.get_choice()
				vres[options[choice]] += 1
		print(vres)

		print('\nПятый этап успешно пройден.')




if option_1 == '4':

	create_key_files_pair(main_password)
	sys.exit(1)
