import pandas as pd
import os
import usaddress
from database import DNCDatabase, ProcessedRecordsDB


class ListStacker():
    input_file_to_dfs = {}
    main_df = None
    dnc_df = None
    duplicates_df = None
    phone_col = 'Phone'
    address_col = 'Address'
    mode = 'Phone'
    seperate_address_after_these_words = [
        "Street", "Avenue",  "Way", "Terrace", "Basement", "Road", "Place", "Circle", "Trail"]

    def __init__(self) -> None:
        self.dnc_db = DNCDatabase()
        self.processed_db = ProcessedRecordsDB()

    def set_settings(self, mode, keyword_filter, keyword_list, is_to_extract_duplicates, remove_dnc_bool, combine_all_list_bool, remove_old_processed_records):
        self.mode = mode
        self.keyword_filter = keyword_filter
        self.keyword_list = keyword_list
        self.is_to_extract_duplicates = is_to_extract_duplicates
        self.remove_dnc_bool = remove_dnc_bool
        self.combine_all_list_bool = combine_all_list_bool
        self.remove_old_processed_records = remove_old_processed_records

    def read_excel(self, file_path, keep_default_na=False):
        df = pd.read_excel(file_path, dtype='string', keep_default_na=keep_default_na)
        return df

    def get_address_part(self, address_parts, part_name):
        part_values = [part[0].strip().strip(',')
                       for part in address_parts if part[1] == part_name]
        return ' '.join(part_values)

    def parse_address(self, address):
        address_parts = usaddress.parse(address)
        parsed_address = pd.Series(dtype='object', )
        parsed_address['Street Address'] = ''
        parsed_address['City'] = self.get_address_part(
            address_parts, 'PlaceName')
        parsed_address['State'] = self.get_address_part(
            address_parts, 'StateName')
        parsed_address['Zipcode'] = self.get_address_part(
            address_parts, 'ZipCode')
        parsed_address['Unit'] = ''

        city_state_zip = parsed_address['City'] + \
            parsed_address['State'] + parsed_address['Zipcode']

        for adr_part in address_parts:
            adr_value = adr_part[0].strip().strip(',')
            if adr_part[1] == 'OccupancyType' or adr_part[1] == 'OccupancyIdentifier':
                parsed_address['Unit'] += f' {adr_value}'
                address = address.replace(adr_value, '')

            if adr_value in city_state_zip:
                address = address.replace(adr_value, '')

        parsed_address['Unit'] = parsed_address['Unit'].strip()
        parsed_address['Street Address'] = address.strip(' ,\n').strip()

        if not parsed_address['City']:
            for keyword in self.seperate_address_after_these_words:
                if keyword.lower() in parsed_address['Street Address'].lower():
                    index = parsed_address['Street Address'].lower().index(
                        keyword.lower())
                    parsed_address['City'] = parsed_address['Street Address'][index +
                                                                              len(keyword):].strip()
                    parsed_address['Street Address'] = parsed_address['Street Address'][:index+len(
                        keyword)]
                    break

        parsed_address['Street Address'] = parsed_address['Street Address'].strip(
            ' ,\n').strip()
        return parsed_address


    def generate_address_column_from_address_parts(self, df):
        df[self.address_col] = df['Street Address'] + ' ' + df['City'] + \
            ' ' + df['State'] + ' ' + df['Zipcode'] + ' ' + df['Unit']
        return df

    def parse_address_to_parts_column(self, df):
        df = df.merge(df[self.address_col].apply(self.parse_address),
                      left_index=True, right_index=True)
        df = self.generate_address_column_from_address_parts(df)
        return df

    @staticmethod
    def format_phone(phone):

        phone_number_digits = ''.join(filter(str.isdigit, phone))

        if phone_number_digits.startswith('1') and len(phone_number_digits) == 11:
            phone_number_digits = phone_number_digits[1:]

        if len(phone_number_digits) == 10:
            phone_number_digits = "({}) {}-{}".format(
                phone_number_digits[:3], phone_number_digits[3:6], phone_number_digits[6:])

        return phone_number_digits

    def format_phone_column(self, df):
        df[self.phone_col] = df[self.phone_col].apply(self.format_phone)
        return df

    def format_input_df(self, df, columns_mapping):

        column_rename_dict = dict((v, k) for k, v in columns_mapping.items())
        df = df[column_rename_dict.keys()]

        df.rename(columns=column_rename_dict, inplace=True)

        if df.empty:
            return df
        
        # Check if Street Address, City, State or Zipcode in column_rename_dict if not then parse the address else just create Address column
        if 'Address' in df:
            df = self.parse_address_to_parts_column(df)
        else:
            df = self.generate_address_column_from_address_parts(df)
        
        df = self.format_phone_column(df)

        df.drop_duplicates(subset=self.mode, keep="last", inplace=True)

        return df

    def get_excel_files(self, folder_path):
        # Check if it is a file then return list with only that file
        files_list = []
        for root, _, files in os.walk(folder_path):
            f_list = [os.path.join(root, file)
                      for file in files if file.endswith('.xlsx')]
            # Make it to get the absolute path
            files_list.extend(f_list)
        return files_list

    def load_input_files(self, folder_path):
        folder_files = self.get_excel_files(folder_path)
        for file_path in folder_files:
            df = self.read_excel(file_path)
            self.input_file_to_dfs[file_path] = df

    def merge_input_file_to_dfs(self):
        all_dfs = self.input_file_to_dfs.values()
        self.main_df = pd.concat(all_dfs)

    def extract_duplicates(self):
        first_instance_duplicates_cond = self.main_df[self.mode].duplicated(
            keep=False)
        self.duplicates_df = self.main_df[first_instance_duplicates_cond]
        duplicate_cond = self.main_df[self.mode].duplicated(keep=False)
        self.main_df = self.main_df[~duplicate_cond]

        for fp, df in self.input_file_to_dfs.items():
            duplicates_indexes = self.duplicates_df[self.mode]
            df = df[~df[self.mode].isin(duplicates_indexes)]
            self.input_file_to_dfs[fp] = df

        # TODO: Improve Logic

    def add_to_dnc(self, dnc_path, dnc_file_map):
        # TODO: Handle empty dataframe
        dnc_df = self.read_excel(dnc_path, keep_default_na=True)
        column_rename_dict = dict((v, k) for k, v in dnc_file_map.items())
        dnc_df = dnc_df[column_rename_dict.keys()]
        dnc_df.rename(columns=column_rename_dict, inplace=True)
        dnc_df = dnc_df[[self.mode]].drop_duplicates().dropna()
        if self.mode == self.address_col:
            dnc_df = self.parse_address_to_parts_column(dnc_df)
        elif self.mode == self.phone_col:
            dnc_df = self.format_phone_column(dnc_df)
        dnc_df = dnc_df[[self.mode]].drop_duplicates().dropna()
        self.dnc_db.insert_records_from_dataframe(self.mode, dnc_df)

    def add_input_to_proccessed_records(self):
        for df in self.input_file_to_dfs.values():
            self.processed_db.insert_records_from_dataframe(self.mode, df)

    def remove_dnc_from_input_dfs(self):
        records = self.dnc_db.get_all_records(self.mode)
        if not records:
            return
        df = pd.DataFrame(records)
        dnc_indexes = df[0]
        for filename, df in self.input_file_to_dfs.items():
            df = df[~df[self.mode].isin(dnc_indexes)]
            self.input_file_to_dfs[filename] = df

    def remove_old_processed_records_from_input_dfs(self):
        records = self.processed_db.get_all_records(self.mode)
        if not records:
            return
        df = pd.DataFrame(records)
        previous_processed_records = df[0]
        for filename, df in self.input_file_to_dfs.items():
            df = df[~df[self.mode].isin(previous_processed_records)]
            self.input_file_to_dfs[filename] = df

    def save_output_files(self, output_folder_path):
        if self.combine_all_list_bool:
            main_fp = os.path.join(output_folder_path, 'main.xlsx')
            if os.path.exists(main_fp):
                raise FileExistsError(main_fp)
            with pd.ExcelWriter(main_fp) as writer:
                self.main_df.to_excel(writer, 'Master', index=False)

                if self.is_to_extract_duplicates:
                    self.duplicates_df.to_excel(
                        writer, 'Extracted Duplicates', index=False)
        else:
            for fp, df in self.input_file_to_dfs.items():
                filename = os.path.basename(fp)
                output_file_path = os.path.join(output_folder_path, filename)
                if os.path.exists(output_file_path):
                    raise FileExistsError(output_file_path)
                df.to_excel(output_file_path, index=False)
            if self.is_to_extract_duplicates:
                duplicate_fp = os.path.join(
                    output_folder_path, 'duplicates.xlsx')
                if os.path.exists(duplicate_fp):
                    raise FileExistsError(duplicate_fp)
                self.duplicates_df.to_excel(duplicate_fp, index=False)
        # TODO: Improve Logic

    def remove_rows_by_keywords(self):
        for fp, df in self.input_file_to_dfs.items():
            mask = ~df.apply(lambda row: any(
                keyword.lower() in str(row.values).lower() for keyword in self.keyword_list), axis=1)
            df = df[mask].reset_index(drop=True)
            self.input_file_to_dfs[fp] = df

    def main(self, file_column_mapping, upload_folder):
        inputs_files = file_column_mapping.get('input_files')
        dnc_files = file_column_mapping.get('dnc_files')

        if dnc_files:
            dnc_fp_file = list(dnc_files.keys())[0]
            dnc_file_map_data = dnc_files[dnc_fp_file]

            self.add_to_dnc(dnc_fp_file, dnc_file_map_data)
        
        self.load_input_files(upload_folder)

        for fp, column_mapping in inputs_files.items():
            df = self.input_file_to_dfs[fp]
            df = self.format_input_df(df, column_mapping)
            self.input_file_to_dfs[fp] = df

        if self.keyword_filter:
            self.remove_rows_by_keywords()

        if self.remove_dnc_bool:
            self.remove_dnc_from_input_dfs()

        if self.remove_old_processed_records:
            self.remove_old_processed_records_from_input_dfs()

        self.merge_input_file_to_dfs()
        if self.is_to_extract_duplicates:
            self.extract_duplicates()

        self.add_input_to_proccessed_records()
        # self.save_output_files(output_folder)

    def close(self):
        self.dnc_db.close_connection()


if __name__ == '__main__':
    self = ListStacker()
    self.parse_address('379 Park Ave, Weehawken, NJ 07086')
    df = pd.DataFrame(
        {'address': ['379 Park Ave, Weehawken, NJ 07086']}
    )
    df.merge(df.address.apply(self.parse_address),
             left_index=True, right_index=True)
