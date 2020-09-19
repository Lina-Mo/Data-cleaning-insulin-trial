#!/usr/bin/env python
# coding: utf-8

# # Oral Insulin Phase II Clinical Trial Data Cleaning 

# ## Gather

# In[1]:


import pandas as pd
import numpy as np


# In[2]:


patients = pd.read_csv('patients.csv')
treatments = pd.read_csv('treatments.csv')
adverse_reactions = pd.read_csv('adverse_reactions.csv')


# ## Assess

# In[3]:


patients


# In[4]:


treatments


# In[5]:


adverse_reactions


# In[6]:


patients.info()


# In[7]:


treatments.info()


# In[8]:


adverse_reactions.info()


# In[9]:


all_columns = pd.Series(list(patients) + list(treatments) + list(adverse_reactions))
all_columns[all_columns.duplicated()]


# In[10]:


list(patients)


# In[11]:


patients[patients['address'].isnull()]


# In[12]:


patients.describe()


# In[13]:


treatments.describe()


# In[14]:


patients.sample(5)


# In[15]:


patients.surname.value_counts()


# In[16]:


patients.address.value_counts()


# In[17]:


patients[patients.address.duplicated()]


# In[18]:


patients.weight.sort_values()


# In[19]:


weight_lbs = patients[patients.surname == 'Zaitseva'].weight * 2.20462
height_in = patients[patients.surname == 'Zaitseva'].height
bmi_check = 703 * weight_lbs / (height_in * height_in)
bmi_check


# In[20]:


patients[patients.surname == 'Zaitseva'].bmi


# In[21]:


sum(treatments.auralin.isnull())


# In[22]:


sum(treatments.novodra.isnull())


# #### Quality
# ##### `patients` table
# - Zip code is a float not a string
# - Zip code has four digits sometimes
# - Tim Neudorf height is 27 in instead of 72 in
# - Full state names sometimes, abbreviations other times
# - Dsvid Gustafsson
# - Missing demographic information (address - contact columns) ***(can't clean yet)***
# - Erroneous datatypes (assigned sex, state, zip_code, and birthdate columns)
# - Multiple phone number formats
# - Default John Doe data
# - Multiple records for Jakobsen, Gersten, Taylor
# - kgs instead of lbs for Zaitseva weight
# 
# ##### `treatments` table
# - Missing HbA1c changes
# - The letter 'u' in starting and ending doses for Auralin and Novodra
# - Lowercase given names and surnames
# - Missing records (280 instead of 350)
# - Erroneous datatypes (auralin and novodra columns)
# - Inaccurate HbA1c changes (leading 4s mistaken as 9s)
# - Nulls represented as dashes (-) in auralin and novodra columns
# 
# ##### `adverse_reactions` table
# - Lowercase given names and surnames

# #### Tidiness
# - Contact column in `patients` table should be split into phone number and email
# - Three variables in two columns in `treatments` table (treatment, start dose and end dose)
# - Adverse reaction should be part of the `treatments` table
# - Given name and surname columns in `patients` table duplicated in `treatments` and `adverse_reactions` tables

# ## Clean

# In[23]:


patients_clean = patients.copy()
treatments_clean = treatments.copy()
adverse_reactions_clean = adverse_reactions.copy()


# ### Missing Data

# #### `treatments`: Missing records (280 instead of 350)

# ##### Define
# Import the cut treatments into a DataFrame and concatenate it with the original treatments DataFrame.

# ##### Code

# In[24]:


treatments_cut = pd.read_csv('treatments_cut.csv')
treatments_clean = pd.concat([treatments_clean, treatments_cut],
                             ignore_index=True)


# ##### Test

# In[25]:


treatments_clean.head()


# In[26]:


treatments_clean.tail()


# #### `treatments`: Missing HbA1c changes and Inaccurate HbA1c changes (leading 4s mistaken as 9s)

# ##### Define
# Recalculate the `hba1c_change` column: `hba1c_start` minus `hba1c_end`. 

# ##### Code

# In[27]:


treatments_clean.hba1c_change = (treatments_clean.hba1c_start - 
                                 treatments_clean.hba1c_end)


# ##### Test

# In[28]:


treatments_clean.hba1c_change.head()


# ### Tidiness

# #### Contact column in `patients` table contains two variables: phone number and email

# ##### Define
# Extract the *phone number* and *email* variables from the *contact* column using regular expressions and pandas' `str.extract` method. Drop the *contact* column when done.

# ##### Code

# In[29]:


patients_clean['phone_number'] = patients_clean.contact.str.extract('((?:\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})', expand=True)
patients_clean['email'] = patients_clean.contact.str.extract('([a-zA-Z][a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.][a-zA-Z]+)', expand=True)
# Note: axis=1 denotes that we are referring to a column, not a row
patients_clean = patients_clean.drop('contact', axis=1)


# ##### Test

# In[30]:


# Confirm contact column is gone
list(patients_clean)


# In[31]:


patients_clean.phone_number.sample(25)


# In[32]:


# Confirm that no emails start with an integer (regex didn't match for this)
patients_clean.email.sort_values().head()


# #### Three variables in two columns in `treatments` table (treatment, start dose and end dose)

# ##### Define
# Melt the *auralin* and *novodra* columns to a *treatment* and a *dose* column (dose will still contain both start and end dose at this point). Then split the dose column on ' - ' to obtain *start_dose* and *end_dose* columns. Drop the intermediate *dose* column.

# ##### Code

# In[33]:


treatments_clean = pd.melt(treatments_clean, id_vars=['given_name', 'surname', 'hba1c_start', 'hba1c_end', 'hba1c_change'],
                           var_name='treatment', value_name='dose')
treatments_clean = treatments_clean[treatments_clean.dose != "-"]
treatments_clean['dose_start'], treatments_clean['dose_end'] = treatments_clean['dose'].str.split(' - ', 1).str
treatments_clean = treatments_clean.drop('dose', axis=1)


# ##### Test

# In[34]:


treatments_clean.head()


# #### Adverse reaction should be part of the `treatments` table

# ##### Define
# Merge the *adverse_reaction* column to the `treatments` table, joining on *given name* and *surname*.

# ##### Code

# In[35]:


treatments_clean = pd.merge(treatments_clean, adverse_reactions_clean,
                            on=['given_name', 'surname'], how='left')


# ##### Test

# In[36]:


treatments_clean


# #### Given name and surname columns in `patients` table duplicated in `treatments` and `adverse_reactions` tables  and Lowercase given names and surnames

# ##### Define
# Adverse reactions table is no longer needed so ignore that part. Isolate the patient ID and names in the `patients` table, then convert these names to lower case to join with `treatments`. Then drop the given name and surname columns in the treatments table (so these being lowercase isn't an issue anymore).

# ##### Code

# In[37]:


id_names = patients_clean[['patient_id', 'given_name', 'surname']]
id_names.given_name = id_names.given_name.str.lower()
id_names.surname = id_names.surname.str.lower()
treatments_clean = pd.merge(treatments_clean, id_names, on=['given_name', 'surname'])
treatments_clean = treatments_clean.drop(['given_name', 'surname'], axis=1)


# ##### Test

# In[38]:


# Confirm the merge was executed correctly
treatments_clean


# In[39]:


# Patient ID should be the only duplicate column
all_columns = pd.Series(list(patients_clean) + list(treatments_clean))
all_columns[all_columns.duplicated()]


# ### Quality

# #### Zip code is a float not a string and Zip code has four digits sometimes

# ##### Define
# Convert the zip code column's data type from a float to a string using `astype`, remove the '.0' using string slicing, and pad four digit zip codes with a leading 0.

# ##### Code

# In[40]:


patients_clean.zip_code = patients_clean.zip_code.astype(str).str[:-2].str.pad(5, fillchar='0')
# Reconvert NaNs entries that were converted to '0000n' by code above
patients_clean.zip_code = patients_clean.zip_code.replace('0000n', np.nan)


# ##### Test

# In[41]:


patients_clean.zip_code.head()


# #### Tim Neudorf height is 27 in instead of 72 in

# ##### Define
# Replace height for rows in the `patients` table that have a height of 27 in (there is only one) with 72 in.

# ##### Code

# In[42]:


patients_clean.height = patients_clean.height.replace(27, 72)


# ##### Test

# In[43]:


# Should be empty
patients_clean[patients_clean.height == 27]


# In[44]:


# Confirm the replacement worked
patients_clean[patients_clean.surname == 'Neudorf']


# #### Full state names sometimes, abbreviations other times

# ##### Define
# Apply a function that converts full state name to state abbreviation for California, New York, Illinois, Florida, and Nebraska.

# ##### Code

# In[45]:


# Mapping from full state name to abbreviation
state_abbrev = {'California': 'CA',
                'New York': 'NY',
                'Illinois': 'IL',
                'Florida': 'FL',
                'Nebraska': 'NE'}

# Function to apply
def abbreviate_state(patient):
    if patient['state'] in state_abbrev.keys():
        abbrev = state_abbrev[patient['state']]
        return abbrev
    else:
        return patient['state']
    
patients_clean['state'] = patients_clean.apply(abbreviate_state, axis=1)


# ##### Test

# In[46]:


patients_clean.state.value_counts()


# #### Dsvid Gustafsson

# ##### Define
# Replace given name for rows in the `patients` table that have a given name of 'Dsvid' with 'David'.

# ##### Code

# In[47]:


patients_clean.given_name = patients_clean.given_name.replace('Dsvid', 'David')


# ##### Test

# In[48]:


patients_clean[patients_clean.surname == 'Gustafsson']


# #### Erroneous datatypes (assigned sex, state, zip_code, and birthdate columns) and Erroneous datatypes (auralin and novodra columns) and The letter 'u' in starting and ending doses for Auralin and Novodra

# ##### Define
# Convert assigned sex and state to categorical data types. Zip code data type was already addressed above. Convert birthdate to datetime data type. Strip the letter 'u' in start dose and end dose and convert those columns to data type integer.

# ##### Code

# In[49]:


# To category
patients_clean.assigned_sex = patients_clean.assigned_sex.astype('category')
patients_clean.state = patients_clean.state.astype('category')

# To datetime
patients_clean.birthdate = pd.to_datetime(patients_clean.birthdate)

# Strip u and to integer
treatments_clean.dose_start = treatments_clean.dose_start.str.strip('u').astype(int)
treatments_clean.dose_end = treatments_clean.dose_end.str.strip('u').astype(int)


# ##### Test

# In[50]:


patients_clean.info()


# In[51]:


treatments_clean.info()


# #### Multiple phone number formats

# ##### Define
# Strip all " ", "-", "(", ")", and "+" and store each number without any formatting. Pad the phone number with a 1 if the length of the number is 10 digits (we want country code).

# ##### Code

# In[52]:


patients_clean.phone_number = patients_clean.phone_number.str.replace(r'\D+', '').str.pad(11, fillchar='1')


# ##### Test

# In[53]:


patients_clean.phone_number.head()


# #### Default John Doe data

# ##### Define
# Remove the non-recoverable John Doe records from the `patients` table.

# ##### Code

# In[54]:


patients_clean = patients_clean[patients_clean.surname != 'Doe']


# ##### Test

# In[55]:


# Should be no Doe records
patients_clean.surname.value_counts()


# In[ ]:


# Should be no 123 Main Street records
patients_clean.address.value_counts()


# #### Multiple records for Jakobsen, Gersten, Taylor

# ##### Define
# Remove the Jake Jakobsen, Pat Gersten, and Sandy Taylor rows from the `patients` table. These are the nicknames, which happen to also not be in the `treatments` table (removing the wrong name would create a consistency issue between the `patients` and `treatments` table). These are all the second occurrence of the duplicate. These are also the only occurences of non-null duplicate addresses.

# ##### Code

# In[ ]:


# tilde means not: http://pandas.pydata.org/pandas-docs/stable/indexing.html#boolean-indexing
patients_clean = patients_clean[~((patients_clean.address.duplicated()) & patients_clean.address.notnull())]


# ##### Test

# In[ ]:


patients_clean[patients_clean.surname == 'Jakobsen']


# In[ ]:


patients_clean[patients_clean.surname == 'Gersten']


# In[ ]:


patients_clean[patients_clean.surname == 'Taylor']


# #### kgs instead of lbs for Zaitseva weight

# ##### Define
# Using [advanced indexing](https://stackoverflow.com/a/44913631) to isolate the row where the surname is Zaitseva and convert the entry in its weight field from kg to lbs.

# ##### Code

# In[ ]:


weight_kg = patients_clean.weight.min()
mask = patients_clean.surname == 'Zaitseva'
column_name = 'weight'
patients_clean.loc[mask, column_name] = weight_kg * 2.20462


# ##### Test

# In[ ]:


# 48.8 shouldn't be the lowest anymore
patients_clean.weight.sort_values()

